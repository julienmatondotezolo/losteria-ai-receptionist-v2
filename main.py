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
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import Response, HTMLResponse
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

# Initialize clients (handle missing credentials for testing)
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio client initialized")
    except Exception as e:
        print(f"❌ Twilio initialization failed: {e}")
else:
    print("⚠️ Twilio credentials missing - voice features disabled (test mode)")

openai_client = None
if OPENAI_API_KEY:
    try:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ OpenAI initialization failed: {e}")
else:
    print("⚠️ OpenAI API key missing - AI features disabled")

# Active call sessions
active_sessions: Dict[str, dict] = {}

# Menu cache
menu_cache = {"data": None, "last_updated": None}

async def fetch_restaurant_menu():
    """Fetch current menu from Ada API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://ada.mindgen.app/api/v1/menu")
            if response.status_code == 200:
                menu_data = response.json()
                menu_cache["data"] = menu_data
                menu_cache["last_updated"] = datetime.now()
                print("✅ Menu fetched successfully")
                return menu_data
            else:
                print(f"❌ Menu fetch error: {response.status_code}")
                return None
    except Exception as e:
        print(f"❌ Menu fetch exception: {e}")
        return None

def format_menu_for_ai(menu_data):
    """Format menu data for AI consumption with comprehensive dish details in Dutch"""
    if not menu_data:
        return "Menu momenteel niet beschikbaar."
    
    formatted = []
    
    # Process each main category
    for category in menu_data:
        cat_names = category.get("names", {})
        cat_name = cat_names.get("nl", cat_names.get("fr", cat_names.get("en", cat_names.get("it", ""))))
        
        if not cat_name or category.get("hidden"):
            continue
            
        formatted.append(f"\n=== {cat_name.upper()} ===")
        
        # Process subcategories
        for subcategory in category.get("subCategories", []):
            if subcategory.get("hidden"):
                continue
                
            subcat_names = subcategory.get("names", {})
            subcat_name = subcat_names.get("nl", subcat_names.get("fr", subcat_names.get("en", subcat_names.get("it", ""))))
            
            if subcat_name:
                formatted.append(f"\n-- {subcat_name} --")
            
            # Process menu items
            for item in subcategory.get("menuItems", []):
                if item.get("hidden"):
                    continue
                    
                item_names = item.get("names", {})
                item_descs = item.get("descriptions", {})
                price = item.get("price", 0)
                
                # Get Dutch name (primary), fallback to others
                name = item_names.get("nl", item_names.get("fr", item_names.get("en", item_names.get("it", ""))))
                desc = item_descs.get("nl", item_descs.get("fr", item_descs.get("en", item_descs.get("it", ""))))
                
                if name:
                    item_line = f"• {name}"
                    if price > 0:
                        item_line += f" - €{price:.2f}".replace(".00", "")
                    if desc:
                        item_line += f" ({desc})"
                    formatted.append(item_line)
                    
                    # Add side dishes if any
                    side_dishes = item.get("sideDishes", [])
                    if side_dishes:
                        sides = []
                        for side in side_dishes:
                            side_names = side.get("names", {})
                            side_name = side_names.get("nl", side_names.get("fr", side_names.get("en", side_names.get("it", ""))))
                            if side_name:
                                sides.append(side_name)
                        if sides:
                            formatted.append(f"  Bijgerechten: {', '.join(sides)}")
                    
                    # Add supplements if any
                    supplements = item.get("supplements", [])
                    if supplements:
                        supp_list = []
                        for supp in supplements:
                            supp_names = supp.get("names", {})
                            supp_name = supp_names.get("nl", supp_names.get("fr", supp_names.get("en", supp_names.get("it", ""))))
                            add_price = supp.get("additionalPrice", 0)
                            if supp_name:
                                if add_price > 0:
                                    supp_list.append(f"{supp_name} (+€{add_price:.2f})".replace(".00", ""))
                                else:
                                    supp_list.append(supp_name)
                        if supp_list:
                            formatted.append(f"  Extra's: {', '.join(supp_list)}")
    
    return "\n".join(formatted)

class CallSession:
    """Manages a single call session with real-time audio processing"""
    
    def __init__(self, call_sid: str, websocket: WebSocket):
        self.call_sid = call_sid
        self.websocket = websocket
        self.conversation_history = []
        self.audio_buffer = b""
        self.is_speaking = False
        self.language = "nl"  # Default to Dutch
        self.call_state = "takeaway"  # Skip language selection, go straight to takeaway
        self.selected_language = "nl"  # Default to Dutch
        self.selected_option = "takeaway"
        
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
        if not openai_client:
            print("⚠️ OpenAI client not available for transcription")
            return "test input"  # Return test input for demo
            
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
        """Generate AI response using GPT-4o with structured call flow"""
        try:
            # Fetch current menu if cache is old or empty
            if (not menu_cache["data"] or 
                not menu_cache["last_updated"] or 
                (datetime.now() - menu_cache["last_updated"]).seconds > 3600):  # 1 hour
                await fetch_restaurant_menu()
            
            # Format current menu for AI
            current_menu = format_menu_for_ai(menu_cache["data"])
            
            # Handle different call states
            if self.call_state == "welcome":
                return await self._handle_welcome_state(user_message)
            elif self.call_state == "language_select":
                return await self._handle_language_selection(user_message)
            elif self.call_state == "menu_select":
                return await self._handle_menu_selection(user_message)
            elif self.call_state == "takeaway":
                return await self._handle_takeaway_flow(user_message, current_menu)
            else:
                return self._get_transfer_message()
                
        except Exception as e:
            print(f"❌ AI generation error: {e}")
            return "Mi dispiace, c'è stato un problema tecnico. La collego al ristorante."
    
    async def _handle_welcome_state(self, user_message: str) -> str:
        """Handle initial welcome and language selection"""
        self.call_state = "language_select"
        return """Benvenuti a L'Osteria Deerlijk! Welcome! Bienvenue!

Please select your language:
- For Dutch, press 1
- For French, press 2  
- For Italian, press 3
- For English, press 4"""
    
    async def _handle_language_selection(self, user_message: str) -> str:
        """Handle language selection"""
        # Detect language choice
        if "1" in user_message or "een" in user_message.lower() or "nederlands" in user_message.lower():
            self.selected_language = "nl"
            self.language = "nl"
            self.call_state = "menu_select"
            return """Dank je wel! Kies een optie:
- Voor afhaal, druk 1
- Voor reservering, druk 2
- Voor andere vragen, druk 3"""
            
        elif "2" in user_message or "deux" in user_message.lower() or "français" in user_message.lower():
            self.selected_language = "fr" 
            self.language = "fr"
            self.call_state = "menu_select"
            return """Merci! Choisissez une option:
- Pour emporter, appuyez sur 1
- Pour réservation, appuyez sur 2
- Pour autres questions, appuyez sur 3"""
            
        elif "3" in user_message or "tre" in user_message.lower() or "italiano" in user_message.lower():
            self.selected_language = "it"
            self.language = "it"
            self.call_state = "menu_select"
            return """Grazie! Scegli un'opzione:
- Per asporto, premi 1
- Per prenotazione, premi 2
- Per altre domande, premi 3"""
            
        elif "4" in user_message or "four" in user_message.lower() or "english" in user_message.lower():
            self.selected_language = "en"
            self.language = "en"
            self.call_state = "menu_select"
            return """Thank you! Choose an option:
- For takeaway, press 1
- For reservation, press 2
- For other questions, press 3"""
        
        else:
            return """Please select your language by pressing:
1 for Dutch, 2 for French, 3 for Italian, 4 for English"""
    
    async def _handle_menu_selection(self, user_message: str) -> str:
        """Handle menu option selection"""
        if "1" in user_message:
            self.selected_option = "takeaway"
            self.call_state = "takeaway"
            return self._get_takeaway_greeting()
            
        elif "2" in user_message or "3" in user_message:
            self.selected_option = "transfer"
            self.call_state = "transfer"
            # Initiate immediate transfer with hold music
            await self.initiate_transfer()
            return self._get_transfer_message()
        
        else:
            # Repeat options in selected language
            if self.selected_language == "nl":
                return "Kies een optie: 1 voor afhaal, 2 voor reservering, 3 voor vragen"
            elif self.selected_language == "fr":
                return "Choisissez: 1 pour emporter, 2 pour réservation, 3 pour questions"
            elif self.selected_language == "it":
                return "Scegli: 1 per asporto, 2 per prenotazione, 3 per domande"
            else:
                return "Choose: 1 for takeaway, 2 for reservation, 3 for questions"
    
    def _get_takeaway_greeting(self) -> str:
        """Get takeaway greeting in selected language"""
        if self.selected_language == "nl":
            return "L'Osteria Deerlijk hier, met Sofia. Hoe kan ik u helpen met uw bestelling?"
        elif self.selected_language == "fr":
            return "L'Osteria Deerlijk ici, c'est Sofia. Comment puis-je vous aider avec votre commande?"
        elif self.selected_language == "it":
            return "L'Osteria Deerlijk, sono Sofia. Come posso aiutarla con il suo ordine?"
        else:
            return "L'Osteria Deerlijk here, this is Sofia. How can I help you with your order?"
    
    def _get_transfer_message(self) -> str:
        """Get transfer message in selected language"""
        if self.selected_language == "nl":
            return "Ik verbind u door met het restaurant. Een moment geduld alstublieft, u wordt niet in de wacht gezet."
        elif self.selected_language == "fr":
            return "Je vous transfère au restaurant. Un moment s'il vous plaît, vous ne serez pas mis en attente."
        elif self.selected_language == "it":
            return "La collego al ristorante. Un momento per favore, non sarà messa in attesa."
        else:
            return "I'm transferring you to the restaurant. One moment please, you will not be put on hold."
    
    async def _handle_takeaway_flow(self, user_message: str, current_menu: str) -> str:
        """Handle takeaway conversation with focus management"""
        # Check if conversation is going off-topic
        off_topic_keywords = ["weather", "politics", "sports", "personal", "meteo", "politiek", "sport", "persoonlijk"]
        if any(keyword in user_message.lower() for keyword in off_topic_keywords):
            if self.selected_language == "nl":
                return "Ik help graag met uw bestelling. Wat zou u willen bestellen van ons menu?"
            elif self.selected_language == "fr":
                return "Je suis là pour vous aider avec votre commande. Que souhaitez-vous commander de notre menu?"
            elif self.selected_language == "it":
                return "Sono qui per aiutarla con il suo ordine. Cosa desidera ordinare dal nostro menu?"
            else:
                return "I'm here to help with your order. What would you like to order from our menu?"
        
        # Build takeaway-focused system prompt with complete restaurant context in Dutch
        system_prompt = f"""Je bent Sofia van L'Osteria Deerlijk en werkt aan de receptie voor afhaalbestellingen.

=== RESTAURANT INFORMATIE ===
- Naam: L'Osteria Deerlijk (authentiek Italiaans restaurant)
- Adres: Stationsstraat 232, 8540 Deerlijk, België
- Telefoon: +32 56 25 63 83
- Website: https://l-osteria.be/
- Geschiedenis: Familie Bombini sinds 1964 (authentieke Italiaanse traditie)
- Specialiteiten: Verse huisgemaakte pasta, Napolitaanse pizza, traditionele Italiaanse keuken

=== OPENINGSUREN ===
- Maandag: GESLOTEN
- Dinsdag: 18:30 - 22:00 (alleen diner)
- Woensdag: 12:00 - 14:00 en 18:30 - 22:00
- Donderdag: 12:00 - 14:00 en 18:30 - 22:00  
- Vrijdag: 12:00 - 14:00 en 18:30 - 22:00
- Zaterdag: 12:00 - 14:00 en 18:30 - 22:00
- Zondag: 18:30 - 22:00 (alleen diner)

=== COMPLETE ACTUELE MENUKAART ===
{current_menu}

=== TAAL EN COMMUNICATIE ===
Klant heeft gekozen voor: {self.selected_language}
Antwoord ALTIJD in het Nederlands

=== PROFESSIONEEL GEDRAG ===
- Je bent Sofia, je werkt in het restaurant (vermeld NOOIT dat je een AI bent)
- Concentreer je UITSLUITEND op afhaalbestellingen
- Bij reserveringen/andere vragen: "Sorry, daarvoor verbind ik u direct door met het restaurant zonder wachttijd"
- Maximaal 2-3 zinnen per antwoord, natuurlijk gesprek
- Wees hartelijk maar professioneel, authentieke Italiaanse stijl
- Stel specifieke gerechten voor uit de menukaart met exacte prijzen
- Ken alle ingrediënten, allergieën, bereidingstijden
- Als je specifieke informatie niet hebt: "Ik verbind u direct door met het restaurant, u hoeft niet te wachten"

=== ANTWOORD RICHTLIJNEN ===
- Herken gerechten bij naam ook als ze verkeerd uitgesproken worden
- Stel bijpassende dranken en bijgerechten voor  
- Vermeld specialiteiten van het huis wanneer relevant
- Help bij keuzes voor allergieën/intoleranties
- Bevestig altijd de totaalprijs aan het einde van de bestelling
- Vraag altijd of ze nog iets anders willen voordat je afsluit

=== VOORBEELDEN COMMUNICATIESTIJL ===
"Wat zou u graag bestellen vanavond?"
"Uitstekende keuze! Onze Spaghetti alle Vongole wordt bereid met verse mosselen"
"Voor voorgerechten kan ik de Burrata met Prosciutto di Parma aanraden"
"Wilt u er nog een dessert bij? Onze Tiramisù wordt in huis gemaakt"""
        
        try:
            print(f"🔍 Debug: user message: {user_message}")
            print(f"🔍 Debug: selected language: {self.selected_language}")
            
            # Always use GPT-4o - no fallback to demo responses
            if openai_client is None:
                error_msg = "GPT-4o not available - service unavailable"
                print(f"❌ {error_msg}")
                # Default Dutch response since Dutch is now the default language
                return "Sorry, de service is momenteel niet beschikbaar. Ik verbind u door met het restaurant."
            
            print("✅ Using GPT-4o for intelligent takeaway responses")
            
            # Add conversation history
            messages = [{"role": "system", "content": system_prompt}]
            for turn in self.conversation_history[-6:]:  # Keep last 6 turns for context
                messages.append(turn)
            messages.append({"role": "user", "content": user_message})
            
            # Generate intelligent response with GPT-4o
            chat_completion = await openai_client.chat.completions.create(
                messages=messages,
                model="gpt-4o",
                temperature=0.8,  # More creative for natural conversation
                max_tokens=250,   # More space for detailed responses
                top_p=0.95,      # Higher quality sampling
                frequency_penalty=0.2,  # Reduce repetition
                presence_penalty=0.3    # Encourage topic variety
            )
            
            response = chat_completion.choices[0].message.content
            print(f"✅ GPT-4o response: {response}")
            
            # Check if AI wants to transfer (doesn't have information)
            transfer_phrases = ["collego al ristorante", "transfer", "don't have", "niet weten", "ne sais pas"]
            if any(phrase in response.lower() for phrase in transfer_phrases):
                self.call_state = "transfer"
                # Initiate call transfer with hold music
                await self.initiate_transfer()
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            print(f"❌ AI generation error: {e}")
            return "Sorry, ik heb dat niet goed begrepen. Kunt u dat herhalen?"
    
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
                        "language": "nl"
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
    
    async def initiate_transfer(self):
        """Initiate call transfer to restaurant with hold music"""
        try:
            if twilio_client:
                print(f"🔄 Initiating transfer for call {self.call_sid}")
                
                # Update the call to redirect to transfer endpoint
                call = twilio_client.calls(self.call_sid).update(
                    url='https://adaphone-v2.mindgen.app/api/voice/transfer',
                    method='POST'
                )
                print(f"✅ Call transfer initiated: {call.sid}")
            else:
                print("⚠️ Twilio client not available for transfer")
                
        except Exception as e:
            print(f"❌ Transfer initiation error: {e}")

@app.post("/api/voice/webhook")
async def voice_webhook(request: Request):
    """Twilio voice webhook - starts Media Streams"""
    form = await request.form()
    call_sid = form.get("CallSid")
    from_number = form.get("From")
    
    print(f"📞 Incoming call from {from_number} (SID: {call_sid})")
    
    # TwiML to start Media Streams in Dutch
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="nl-NL">
        Hallo! Welkom bij L'Osteria Deerlijk. Een ogenblik geduld...
    </Say>
    <Connect>
        <Stream url="wss://adaphone-v2.mindgen.app/ws/media/{call_sid}" />
    </Connect>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/api/voice/transfer")
async def voice_transfer(request: Request):
    """Handle call transfer with hold music"""
    form = await request.form()
    call_sid = form.get("CallSid")
    
    print(f"🔄 Transferring call {call_sid} to restaurant with hold music")
    
    # TwiML to transfer call with professional hold experience in Dutch
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="nl-NL">
        Ik verbind u door met restaurant L'Osteria Deerlijk. Een moment geduld, u blijft in de lijn.
    </Say>
    <Pause length="2"/>
    <Say voice="alice" language="nl-NL" rate="slow">
        Verbinding wordt gemaakt... U wordt doorverbonden...
    </Say>
    <Pause length="3"/>
    <Say voice="alice" language="nl-NL" rate="slow">
        Wij verbinden u door met het restaurant...
    </Say>
    <Pause length="2"/>
    <Dial timeout="25" action="/api/voice/no-answer">
        <Number>{RESTAURANT_PHONE}</Number>
    </Dial>
    <Say voice="alice" language="nl-NL">
        Sorry, het restaurant neemt momenteel niet op. Probeert u het later opnieuw.
    </Say>
    <Hangup />
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/api/voice/no-answer")
async def voice_no_answer(request: Request):
    """Handle when restaurant doesn't answer"""
    form = await request.form()
    call_sid = form.get("CallSid")
    
    print(f"📞 Restaurant didn't answer for call {call_sid}")
    
    # TwiML to handle no answer in Dutch
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="nl-NL">
        Sorry, het restaurant neemt momenteel niet op. Onze openingstijden zijn: dinsdag van 18:30 tot 22:00, woensdag-zaterdag van 12:00 tot 14:00 en van 18:30 tot 22:00, zondag van 18:30 tot 22:00. Wij zijn gesloten op maandag. Bedankt voor het bellen naar L'Osteria Deerlijk.
    </Say>
    <Hangup />
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
                # Send welcome message in Dutch (default language)
                welcome = "Hallo! Met Sofia van L'Osteria Deerlijk. Hoe kan ik u helpen met uw bestelling?"
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

@app.get("/")
async def serve_test_interface():
    """Serve the test interface"""
    with open("test_interface.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "active_calls": len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/test-gpt")
async def test_gpt():
    """Test GPT-4o functionality"""
    try:
        if openai_client is None:
            return {"error": "OpenAI client not initialized", "gpt4o_available": False}
        
        # Test GPT-4o with a simple restaurant question in Dutch
        response = await openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Je bent Sofia van L'Osteria Deerlijk. Antwoord in het Nederlands."},
                {"role": "user", "content": "Wat raadt u aan voor pasta?"}
            ],
            model="gpt-4o",
            temperature=0.7,
            max_tokens=100
        )
        
        return {
            "gpt4o_available": True,
            "test_response": response.choices[0].message.content,
            "model_used": response.model,
            "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
        }
    except Exception as e:
        return {"error": str(e), "gpt4o_available": False}

@app.post("/api/chat")
async def chat_with_gpt4o(request: Request):
    """Chat with GPT-4o with conversation memory for test interface"""
    try:
        form = await request.form()
        user_message = form.get("message", "")
        session_id = form.get("session_id", "test_session")
        
        if not user_message:
            return {"error": "No message provided"}
        
        if openai_client is None:
            return {"error": "GPT-4o not available", "response": "Sorry, de service is momenteel niet beschikbaar."}
        
        # Get or create conversation history for this session
        if session_id not in active_sessions:
            # Create a mock call session for testing
            from unittest.mock import MagicMock
            mock_websocket = MagicMock()
            mock_websocket.send_text = MagicMock()
            
            active_sessions[session_id] = CallSession(session_id, mock_websocket)
        
        session = active_sessions[session_id]
        
        # Fetch current menu if needed
        if (not menu_cache["data"] or 
            not menu_cache["last_updated"] or 
            (datetime.now() - menu_cache["last_updated"]).seconds > 3600):
            await fetch_restaurant_menu()
        
        current_menu = format_menu_for_ai(menu_cache["data"])
        
        # Use the same takeaway flow as the real system
        response = await session._handle_takeaway_flow(user_message, current_menu)
        
        return {
            "response": response,
            "session_id": session_id,
            "conversation_length": len(session.conversation_history)
        }
        
    except Exception as e:
        print(f"❌ Chat API error: {e}")
        return {"error": str(e), "response": "Sorry, er is een fout opgetreden."}

@app.get("/api/status")
async def get_status():
    """Get service status and active calls"""
    return {
        "service": "L'Osteria AI Receptionist v2",
        "stack": "FastAPI + Twilio Media Streams + GPT-4o + Cartesia",
        "active_calls": len(active_sessions),
        "call_sessions": list(active_sessions.keys()),
        "menu_last_updated": menu_cache["last_updated"].isoformat() if menu_cache["last_updated"] else None,
        "menu_available": bool(menu_cache["data"]),
        "call_flow": "Direct Dutch Takeaway Flow (Skip Language Selection)",
        "features": [
            "Structured call flow with language selection",
            "GPT-4o restaurant intelligence", 
            "Live menu integration (internal)",
            "Takeaway order management",
            "Professional call transfer",
            "Cartesia ultra-low latency TTS",
            "Async WebSocket architecture",
            "Multilingual support (NL/FR/IT/EN)"
        ]
    }

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("🚀 Starting L'Osteria AI Receptionist v2...")
    print("📋 Stack: FastAPI + Twilio Media Streams + GPT-4o + Cartesia")
    print("📋 Fetching initial menu...")
    await fetch_restaurant_menu()
    print("✅ Service initialized")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5011,  # Temporary port for testing
        reload=True,
        log_level="info"
    )