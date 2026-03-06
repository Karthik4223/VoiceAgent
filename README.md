# Real-Time Multilingual Voice AI Agent

A clinical appointment booking agent built with Python, FastAPI, and Deepgram/OpenAI.

## Architecture

```
User Speech -> Deepgram STT -> Gemini 1.5 Flash Agent Reasoning (Tool Calling) -> SQL DB (SQLite) -> Deepgram TTS -> Audio Response
```

### Key Components
- **FastAPI**: Backend framework and WebSocket server.
- **Deepgram**: Low-latency Speech-to-Text and Text-to-Speech ($200 credit).
- **Gemini**: State-of-the-art multimodal reasoning with tool calling.
- **Redis**: Session memory and persistent user preferences.
- **SQLAlchemy/SQLite**: Appointment and doctor data storage.

## Features
- **Booking/Rescheduling/Cancellation**: Managed via AI tool calling.
- **Multilingual Support**: Supports English, Hindi, and Tamil.
- **Low Latency**: Design optimized for < 450ms turnaround.
- **Outbound Campaigns**: Proactive reminders and follow-ups.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Environment Variables**:
   Copy `backend/.env.example` to `backend/.env` and fill in:
   - `OPENAI_API_KEY`
   - `DEEPGRAM_API_KEY`

3. **Database Seeding**:
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   python3 scripts/seed_db.py
   ```

4. **Run Server**:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

## Latency Measurement
We track latency at each stage:
- **STT**: ~100-150ms 
- **LLM Reasoning**: ~150-250ms
- **TTS Generation**: ~100ms
- **Total**: ~350-500ms (depending on LLM complexity)

Metrics are logged for every interaction in the console and sent via WebSocket.
