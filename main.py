#!/usr/bin/env python3
"""
L'Osteria AI Receptionist v2 - Real-time Conversational System
Stack: FastAPI + Twilio Media Streams + Groq + Cartesia + WebSockets
"""

import asyncio
import json
import base64
import os
from typing import Dict, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from twilio.rest import Client
from openai import AsyncOpenAI
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="L'Osteria AI Receptionist v2", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
RESTAURANT_PHONE = os.getenv("RESTAURANT_PHONE", "+32562563983")

# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Active call sessions
active_sessions: Dict[str, dict] = {}

class CallSession:
    """Manages a single call session with real-time audio processing"""
    
    def __init__(self, call_sid: str, websocket: WebSocket):
        self.call_sid = call_sid
        self.websocket = websocket
        self.conversation_history = []
        self.audio_buffer = b""
        self.is_speaking = False
        self.language = "it"  # Default to Italian for L'Osteria
        
    async def process_audio_chunk(self, audio_data: bytes):
        """Process incoming audio chunk for transcription"""
        self.audio_buffer += audio_data
        
        # Process when we have enough audio (every ~1 second)
        if len(self.audio_buffer) > 16000:  # ~1 second at 16kHz
            await self.transcribe_and_respond()
            self.audio_buffer = b""
    
    async def transcribe_and_respond(self):
        """Transcribe audio and generate AI response"""
        if not self.audio_buffer:
            return
            
        try:
            # Transcribe with Groq (faster than OpenAI)
            transcription = await self.transcribe_audio(self.audio_buffer)
            if not transcription.strip():
                return
                
            print(f"🎤 Customer said: {transcription}")
            
            # Generate AI response
            response = await self.generate_ai_response(transcription)
            print(f"🤖 AI responds: {response}")
            
            # Convert to speech and stream
            await self.speak_response(response)
            
        except Exception as e:
            print(f"❌ Error in transcribe_and_respond: {e}")
    
    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Transcribe audio using OpenAI Whisper"""
        try:
            # Create audio file for OpenAI API
            from io import BytesIO
            audio_file = BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            
            # Use OpenAI's Whisper model
            transcription = await openai_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                language=self.language
            )
            
            return transcription.text
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""
    
    async def generate_ai_response(self, user_message: str) -> str:
        """Generate AI response using GPT-4o"""
        try:
            # Build conversation context with restaurant knowledge
            system_prompt = """Sei la receptionist AI de L'Osteria Deerlijk, un ristorante italiano autentico.
            
Informazioni ristorante:
- Nome: L'Osteria Deerlijk  
- Indirizzo: Stationsstraat 232, 8540 Deerlijk, Belgio
- Telefono: +32 56 25 63 83
- Famiglia Bombini dal 1964 (tradizione autentica)
- Chiuso: lunedì e domenica
- Cucina: italiana autentica, specialità di pesce fresco
- Atmosfera: familiare, tradizionale, accogliente

Menu highlights:
- Antipasti: bruschette, antipasto misto, crudo di tonno
- Primi: risotto ai frutti di mare, spaghetti alle vongole, pasta fresca fatta in casa
- Secondi: branzino al sale, orata alla griglia, osso buco alla milanese
- Dolci: tiramisu della casa, panna cotta, cannoli siciliani
- Vini: selezione italiana (Chianti, Prosecco, Barolo)

Comportamento:
- Rispondi nella lingua del cliente (italiano, olandese, francese)
- Caldo e accogliente come la famiglia Bombini
- Per prenotazioni: "La collego subito con il ristorante"
- Per menu: descrivi con passione i piatti della tradizione
- Suggerisci abbinamenti vino-cibo se richiesto
- Menziona allergie/restrizioni dietetiche se necessario
- Massimo 2-3 frasi per risposta
- Se non capisci: "Scusi, può ripetere per favore?"

Esempi:
- "Benvenuti! Come posso aiutarvi oggi?"
- "Il nostro risotto ai frutti di mare è preparato con pesce freschissimo del giorno"
- "Per le prenotazioni la metto in contatto direttamente con il ristorante"
            
            # Add conversation history
            messages = [{"role": "system", "content": system_prompt}]
            for turn in self.conversation_history[-8:]:  # Keep last 8 turns for context
                messages.append(turn)
            messages.append({"role": "user", "content": user_message})
            
            # Generate response with GPT-4o
            chat_completion = await openai_client.chat.completions.create(
                messages=messages,
                model="gpt-4o",
                temperature=0.7,
                max_tokens=200,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            response = chat_completion.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            print(f"❌ AI generation error: {e}")
            return "Mi dispiace, non ho capito bene. Può ripetere per favore?"
    
    async def speak_response(self, text: str):
        """Convert text to speech using Cartesia and stream to call"""
        try:
            # Use Cartesia for ultra-low latency TTS
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.cartesia.ai/tts/bytes",
                    headers={
                        "Cartesia-Version": "2024-06-10",
                        "X-API-Key": CARTESIA_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "model_id": "sonic-multilingual",
                        "transcript": text,
                        "voice": {
                            "mode": "id",
                            "id": "a0e99841-438c-4a64-b679-ae501e7d6091"  # Warm Italian female voice
                        },
                        "output_format": {
                            "container": "raw",
                            "encoding": "pcm_mulaw",
                            "sample_rate": 8000
                        },
                        "language": "it"
                    }
                )
                
                if response.status_code == 200:
                    audio_data = response.content
                    await self.stream_audio_to_call(audio_data)
                else:
                    print(f"❌ TTS error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"❌ Speech synthesis error: {e}")
    
    async def stream_audio_to_call(self, audio_data: bytes):
        """Stream audio data to Twilio call via WebSocket"""
        try:
            # Encode audio for Twilio Media Streams
            audio_b64 = base64.b64encode(audio_data).decode()
            
            # Send audio to Twilio
            message = {
                "event": "media",
                "streamSid": self.call_sid,
                "media": {
                    "payload": audio_b64
                }
            }
            
            await self.websocket.send_text(json.dumps(message))
            
        except Exception as e:
            print(f"❌ Audio streaming error: {e}")

@app.post("/api/voice/webhook")
async def voice_webhook(request: Request):
    """Twilio voice webhook - starts Media Streams"""
    form = await request.form()
    call_sid = form.get("CallSid")
    from_number = form.get("From")
    
    print(f"📞 Incoming call from {from_number} (SID: {call_sid})")
    
    # TwiML to start Media Streams
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="it-IT">
        Ciao! Benvenuti a L'Osteria Deerlijk. Un momento prego...
    </Say>
    <Connect>
        <Stream url="wss://adaphone-v2.mindgen.app/ws/media/{call_sid}" />
    </Connect>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.websocket("/ws/media/{call_sid}")
async def websocket_media_handler(websocket: WebSocket, call_sid: str):
    """Handle Twilio Media Streams WebSocket connection"""
    await websocket.accept()
    print(f"🔌 WebSocket connected for call {call_sid}")
    
    # Create call session
    session = CallSession(call_sid, websocket)
    active_sessions[call_sid] = session
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types from Twilio
            event = message.get("event")
            
            if event == "connected":
                print(f"✅ Media stream connected for {call_sid}")
                
            elif event == "start":
                print(f"🎬 Media stream started for {call_sid}")
                # Send welcome message
                welcome = "Ciao! Sono l'assistente di L'Osteria. Come posso aiutarla?"
                await session.speak_response(welcome)
                
            elif event == "media":
                # Process incoming audio
                media = message.get("media", {})
                payload = media.get("payload", "")
                if payload:
                    # Decode base64 audio
                    audio_data = base64.b64decode(payload)
                    await session.process_audio_chunk(audio_data)
                    
            elif event == "stop":
                print(f"🛑 Media stream stopped for {call_sid}")
                break
                
    except WebSocketDisconnect:
        print(f"📴 WebSocket disconnected for {call_sid}")
    except Exception as e:
        print(f"❌ WebSocket error for {call_sid}: {e}")
    finally:
        # Cleanup session
        if call_sid in active_sessions:
            del active_sessions[call_sid]
        print(f"🧹 Cleaned up session {call_sid}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "active_calls": len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def get_status():
    """Get service status and active calls"""
    return {
        "service": "L'Osteria AI Receptionist v2",
        "stack": "FastAPI + Twilio Media Streams + GPT-4o + Cartesia",
        "active_calls": len(active_sessions),
        "call_sessions": list(active_sessions.keys()),
        "features": [
            "Real-time conversation",
            "GPT-4o restaurant intelligence", 
            "Cartesia ultra-low latency TTS",
            "Async WebSocket architecture",
            "Multilingual support (IT/NL/FR)"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting L'Osteria AI Receptionist v2...")
    print("📋 Stack: FastAPI + Twilio Media Streams + GPT-4o + Cartesia")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5010,  # New port for v2
        reload=True,
        log_level="info"
    )