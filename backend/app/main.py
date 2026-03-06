import os
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger
from dotenv import load_dotenv

from backend.app.models.database import init_db
from backend.app.memory.manager import MemoryManager
from backend.app.services.voice_service import VoiceService
from backend.app.services.agent_service import AgentService

load_dotenv()

app = FastAPI(title="Voice AI Clinical Agent")

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
            
            # 1. STT
            stt_result = await voice_service.transcribe_audio(data)
            user_text = stt_result.get("text")
            if not user_text:
                continue
                
            logger.info(f"User: {user_text}")
            
            # 2. Reasoning
            patient_context = {"phone": phone}
            ai_text = await agent_service.run_reasoning(user_text, history, patient_context)
            logger.info(f"AI: {ai_text}")
            
            # 3. TTS
            # Detect language for better voice selection
            lang = await voice_service.detect_language(ai_text)
            audio_response = await voice_service.synthesize_speech(ai_text, language=lang)
            
            # 4. End-to-End Latency
            end_pipeline = time.time()
            total_latency = (end_pipeline - start_pipeline) * 1000
            
            # 5. Send Audio and Metrics
            await websocket.send_bytes(audio_response)
            await websocket.send_json({
                "text": ai_text,
                "latency_ms": total_latency,
                "stt_latency": stt_result.get("latency"),
                "log": f"Total Latency: {total_latency:.2f}ms"
            })
            
            # Update history
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": ai_text})
            memory_manager.update_session(session_id, {"history": history[-10:]}) # Keep last 10 turns
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket session ended: {session_id}")
    except Exception as e:
        logger.error(f"Error in websocket: {e}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
