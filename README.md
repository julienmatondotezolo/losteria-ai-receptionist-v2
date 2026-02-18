# L'Osteria AI Receptionist v2

**Real-time conversational AI receptionist with ultra-low latency**

## 🚀 Tech Stack

- **FastAPI + WebSockets** - Async Python backend
- **Twilio Media Streams** - Real-time audio streaming
- **GPT-4o** - Superior restaurant intelligence & natural conversation
- **Cartesia Sonic** - Ultra-low latency TTS (100ms response)
- **Async Architecture** - Handle multiple calls simultaneously

## ✨ Features

- 🎙️ **Real-time conversation** (no menu prompts)
- ⚡ **Ultra-fast response** with Cartesia TTS (100ms)
- 🇮🇹🇳🇱🇫🇷 **Multilingual** (Italian, Dutch, French)
- 📞 **Multi-call handling** with async WebSockets
- 🍝 **Live menu integration** fetches from Ada API (ada.mindgen.app/api/v1/menu)
- 🧠 **Restaurant intelligence** with GPT-4o menu knowledge
- 🔄 **Seamless transfers** to restaurant staff

## 🆚 vs v1 Comparison

| Feature | v1 (Current) | v2 (New) |
|---------|-------------|----------|
| **Architecture** | Node.js webhook | Python async WebSocket |
| **Conversation** | Menu prompts | Real-time chat |
| **Response Time** | 2-3 seconds | ~100ms |
| **Concurrency** | Blocking calls | Async multi-call |
| **AI Model** | GPT-4 (basic) | GPT-4o (restaurant optimized) |
| **TTS** | Twilio basic | Cartesia (broadcast quality) |
| **Experience** | Phone tree | Natural conversation |

## 🛠️ Setup

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Install Python dependencies  
pip install -r requirements.txt
```

### 2. API Keys Required

```bash
# API keys required:
OPENAI_API_KEY=sk-...       # platform.openai.com
CARTESIA_API_KEY=...        # cartesia.ai
```

### 3. Local Development

```bash
# Start development server
python main.py

# Test health check
curl http://localhost:5010/api/health
```

### 4. Test Interface

```bash
# Start local server
python main.py

# Open test interface in browser
open http://localhost:5010
```

The test interface provides:
- **Call Button** to simulate incoming calls
- **Number pad** for option selection (1-4)
- **Text input** for natural conversation
- **Flow visualization** showing call states
- **Language switching** testing

### 5. VPS Deployment

```bash
# Upload to VPS
scp -r . root@46.224.93.79:/root/app/adaphone-v2/

# Install dependencies on VPS
ssh root@46.224.93.79 "cd /root/app/adaphone-v2 && pip install -r requirements.txt"

# Start with PM2
ssh root@46.224.93.79 "cd /root/app/adaphone-v2 && pm2 start ecosystem.config.js"
```

### 5. Nginx Configuration

```nginx
# Add to nginx sites-enabled
server {
    listen 443 ssl;
    server_name adaphone-v2.mindgen.app;
    
    location / {
        proxy_pass http://127.0.0.1:5010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket support for Media Streams
    location /ws/ {
        proxy_pass http://127.0.0.1:5010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🎯 Structured Call Flow

1. **Welcome** → Multilingual greeting, language selection (1-4)
2. **Language Selection:**
   - Dutch (1) / French (2) / Italian (3) / English (4)
3. **Menu Options** (in selected language):
   - Takeaway (1) → Sofia AI assistant
   - Reservation (2) → Transfer to restaurant
   - Other Questions (3) → Transfer to restaurant
4. **Takeaway Flow:**
   - Natural conversation with Sofia
   - Live menu integration from Ada API
   - Order assistance with focus management
   - Professional transfer if needed (no hold)
5. **Transfer Flow:**
   - "You will not be put on hold"
   - Immediate connection to restaurant

## 🔧 Configuration

### Voice Selection
- **Cartesia Voice ID**: `a0e99841-438c-4a64-b679-ae501e7d6091` (Warm Italian female)
- **Language**: Italian (`it`)
- **Audio Format**: PCM µ-law, 8kHz (Twilio compatible)

### AI Personality
- Warm, professional Italian receptionist
- Family restaurant vibe (Bombini since 1964)
- Brief responses (max 2 sentences)
- Handles: bookings, menu, hours, directions

## 📊 Monitoring & Testing

```bash
# Test interface (browser)
open http://localhost:5010
# or https://adaphone-v2.mindgen.app

# Check service status
curl https://adaphone-v2.mindgen.app/api/status

# Monitor PM2 logs
pm2 logs adaphone-v2

# Active call sessions
curl https://adaphone-v2.mindgen.app/api/health
```

## 🔄 Migration Strategy

1. **Phase 1**: Deploy v2 on port 5010 (parallel to v1)
2. **Phase 2**: Test extensively with dedicated number
3. **Phase 3**: Update Twilio webhook to point to v2
4. **Phase 4**: Monitor for 24h, rollback if issues
5. **Phase 5**: Decommission v1

## 🚨 Rollback Plan

If issues arise:
```bash
# Revert Twilio webhook to v1
# Update: https://adaphone.mindgen.app/api/voice/webhook

# Stop v2 service
pm2 stop adaphone-v2
```

## 🎭 Testing

Test the new system:
- **Health**: `GET /api/health`
- **Status**: `GET /api/status` 
- **WebSocket**: Connect to `/ws/media/test123`
- **Voice**: Call the Twilio number once deployed

---

**Goal**: Transform L'Osteria's phone experience from robotic menu navigation to natural conversation that feels like talking to a real Italian receptionist. 🇮🇹✨