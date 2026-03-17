import os
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
from dotenv import load_dotenv

from backend.app.models.database import init_db
from backend.app.memory.manager import MemoryManager
from backend.app.services.voice_service import VoiceService
from backend.app.services.agent_service import AgentService
from backend.app.services.database_service import db_service

load_dotenv()

app = FastAPI(title="Voice AI Clinical Agent")

# Serve frontend
@app.get("/")
async def get_frontend():
    return FileResponse("frontend/index.html")

# Global instances
memory_manager = MemoryManager()
voice_service = VoiceService()
agent_service = AgentService()

@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Database initialized")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/history")
async def get_history():
    return await db_service.get_previous_conversations()

@app.websocket("/ws/voice")
async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
    await websocket.accept()
    logger.info(f"WebSocket session started: {session_id}")
    
    # Store history in memory
    session_data = memory_manager.get_session(session_id)
    history = session_data.get("history", [])
    phone = session_data.get("phone", "9876543210") # Mock phone for demo
    
    try:
        while True:
            # Receive audio chunk (bytes)
            data = await websocket.receive_bytes()
            
            # Simple VAD or assume full phrase for the demo
            # In a real system, we'd stream chunks to Deepgram and wait for final results
            
            # Start Pipeline Timing
            start_pipeline = time.time()
            
            # Stage 1: STT
            await websocket.send_json({"type": "status_update", "stage": "STT", "message": "Deepgram STT: Transcribing..."})
            stt_start = time.time()
            stt_result = await voice_service.transcribe_audio(data)
            stt_latency = (time.time() - stt_start) * 1000
            user_text = stt_result.get("text")
            
            if not user_text:
                await websocket.send_json({"type": "status_update", "stage": "IDLE", "message": "No speech detected"})
                continue
                
            logger.info(f"User Transcribed: {user_text}")
            await websocket.send_json({
                "type": "user_transcript",
                "text": user_text,
                "latency": stt_latency
            })
            
            # Stage 2: Reasoning
            await websocket.send_json({"type": "status_update", "stage": "LLM", "message": "Gemini 1.5: Reasoning..."})
            llm_start = time.time()
            ai_text = await agent_service.run_reasoning(user_text, history, {"phone": phone})
            llm_latency = (time.time() - llm_start) * 1000
            
            # Stage 3: TTS
            await websocket.send_json({"type": "status_update", "stage": "TTS", "message": "Deepgram TTS: Synthesizing..."})
            tts_start = time.time()
            lang = await voice_service.detect_language(ai_text)
            audio_response = await voice_service.synthesize_speech(ai_text, language=lang)
            tts_latency = (time.time() - tts_start) * 1000
            
            total_latency = (time.time() - start_pipeline) * 1000
            
            # Send Results
            await websocket.send_bytes(audio_response)
            await websocket.send_json({
                "type": "ai_response",
                "text": ai_text,
                "metrics": {
                    "stt": stt_latency,
                    "llm": llm_latency,
                    "tts": tts_latency,
                    "total": total_latency
                }
            })
            # Update history
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": ai_text})
            memory_manager.update_session(session_id, {"history": history[-10:]}) # Keep last 10 turns
            
            # Store in ChromaDB
            await db_service.store_interaction(session_id, "user", user_text)
            await db_service.store_interaction(session_id, "assistant", ai_text)
            
            await websocket.send_json({"type": "status_update", "stage": "REPLYING", "message": "Agent Speaking"})
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket session ended: {session_id}")
    except Exception as e:
        logger.error(f"Error in websocket: {e}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
