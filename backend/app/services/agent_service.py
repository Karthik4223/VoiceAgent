import os
import json
import time
from typing import List, Dict, Any
import google.generativeai as genai
from loguru import logger
from backend.app.tools.appointment_tools import get_doctors, check_availability, book_appointment, cancel_appointment

class AgentService:
    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=gemini_key)
        
        # Tools definitions removed for general talk bot
        self.tools = []
        
        self.model = genai.GenerativeModel(
            model_name="gemini-flash-latest"  #"gemini-1.5-flash"
        )

    async def run_reasoning(self, user_input: str, history: List[Dict[str, str]], context: Dict[str, Any]) -> str:
        start_time = time.time()
        
        system_prompt = """
        You are a friendly and helpful AI assistant. 
        You can talk about anything the user wants. 
        There are no restrictions on topics. 
        Keep your responses concise and engaging for a voice conversation.
        Support English, Hindi, and Telugu. Respond in the same language as the user.
        """
        
        # Convert history for Gemini
        gemini_history = []
        for h in history:
            role = "user" if h["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [h["content"]]})
            
        chat = self.model.start_chat(history=gemini_history)
        
        try:
            response = await chat.send_message_async(f"System Message: {system_prompt}\n\nUser: {user_input}")
            content = response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return "I'm sorry, I'm having trouble thinking right now."

        latency = (time.time() - start_time) * 1000
        logger.info(f"Gemini Reasoning Latency: {latency:.2f}ms")
        return content
