import os
import aiohttp
import json
from loguru import logger
import time

class VoiceService:
    def __init__(self):
        self.dg_api_key = os.getenv("DEEPGRAM_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    async def transcribe_audio(self, audio_data: bytes) -> dict:
        """Transcribes audio using Deepgram for low latency."""
        start_time = time.time()
        if not self.dg_api_key:
            return {"text": "", "error": "Deepgram key missing"}
            
        url = "https://api.deepgram.com/v1/listen?smart_format=true&model=nova-2&language=en-US" # Default to en, can be changed
        headers = {
            "Authorization": f"Token {self.dg_api_key}",
            "Content-Type": "audio/wav" # Adjust based on input
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=audio_data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
                    latency = (time.time() - start_time) * 1000
                    logger.info(f"STT Latency: {latency:.2f}ms")
                    return {"text": transcript, "latency": latency}
                else:
                    return {"text": "", "error": await resp.text()}

    async def synthesize_speech(self, text: str, language: str = "en") -> bytes:
        """Synthesizes speech using Deepgram Aura."""
        start_time = time.time()
        if not self.dg_api_key:
            return b""
            
        # Select voice based on language
        # Note: Deepgram Aura is best for English. 
        # For Hindi/Tamil, consider OpenAI or specialized TTS.
        voice = "aura-asteria-en"
        if language == "hi":
            voice = "aura-stella-en" # Placeholder - Deepgram is expanding multi-lang
        elif language == "ta":
            voice = "aura-stella-en" # Placeholder
            
        url = f"https://api.deepgram.com/v1/speak?model={voice}"
        headers = {
            "Authorization": f"Token {self.dg_api_key}",
            "Content-Type": "application/json"
        }
        payload = {"text": text}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    audio_content = await resp.read()
                    latency = (time.time() - start_time) * 1000
                    logger.info(f"TTS Latency ({language}): {latency:.2f}ms")
                    return audio_content
                else:
                    logger.error(f"TTS Error: {await resp.text()}")
                    return b""
                    
    async def detect_language(self, text: str) -> str:
        """Detect language if not already known."""
        # Simple implementation using langdetect or LLM check
        from langdetect import detect
        try:
            lang = detect(text)
            if lang in ["en", "hi", "ta"]:
                return lang
            return "en"
        except:
            return "en"
