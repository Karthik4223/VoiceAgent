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
        
        # Tools definitions for Gemini
        self.tools = [
            get_doctors,
            check_availability,
            book_appointment,
            cancel_appointment
        ]
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=self.tools
        )

    async def run_reasoning(self, user_input: str, history: List[Dict[str, str]], patient_context: Dict[str, Any]) -> str:
        start_time = time.time()
        
        system_prompt = f"""
        You are an AI Clinical Appointment Booking Assistant. 
        You help patients book, reschedule, and cancel appointments.
        Current Patient Context: {json.dumps(patient_context)}
        
        Rules:
        - Be professional and helpful.
        - Support English, Hindi, and Tamil. Respond in the same language as the user.
        - Always check availability before booking.
        - If a slot is taken, suggest alternatives.
        - Today's date is {time.strftime("%Y-%m-%d")}.
        """
        
        # Convert history for Gemini
        gemini_history = []
        for h in history:
            role = "user" if h["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [h["content"]]})
            
        chat = self.model.start_chat(history=gemini_history)
        
        # Add system instruction via content if not supported as native system_instruction in start_chat
        try:
            response = await chat.send_message_async(f"System Context: {system_prompt}\n\nUser: {user_input}")
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return "I'm sorry, I'm having trouble thinking right now."

        # Handle tool calls
        while response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
            fc = response.candidates[0].content.parts[0].function_call
            function_name = fc.name
            function_args = fc.args
            
            logger.info(f"Gemini calling tool: {function_name} with {function_args}")
            
            # Simplified tool execution lookup
            if function_name == "get_doctors":
                tool_result = await get_doctors()
            elif function_name == "check_availability":
                tool_result = await check_availability(function_args['doctor_id'], function_args['date'])
            elif function_name == "book_appointment":
                phone = patient_context.get("phone", "unknown")
                tool_result = await book_appointment(phone, int(function_args['doctor_id']), function_args['date'], function_args['time'])
            elif function_name == "cancel_appointment":
                tool_result = await cancel_appointment(int(function_args['appointment_id']))
            else:
                tool_result = {"error": "Unknown tool"}

            # Send tool response back to Gemini
            response = await chat.send_message_async(
                genai.types.Content(
                    parts=[genai.types.Part.from_function_response(
                        name=function_name,
                        response=tool_result
                    )]
                )
            )

        content = response.text
        latency = (time.time() - start_time) * 1000
        logger.info(f"Gemini Reasoning Latency: {latency:.2f}ms")
        return content
