# 🍝 L'Osteria AI Receptionist v2

Revolutionary GPT-4o powered phone receptionist for L'Osteria Deerlijk with real-time conversation, complete menu knowledge, and professional Dutch service.

## ✨ Key Features

- 🧠 **GPT-4o Intelligence** - Real conversation memory, no demo patterns
- 🇳🇱 **Dutch Default** - Native Dutch language throughout entire system
- 📋 **Complete Menu Knowledge** - Live integration with Ada menu API
- 📞 **Professional Call Transfer** - Hold music and seamless handoff
- 🎯 **Direct Takeaway Flow** - Skip language selection, instant service
- ⚡ **Real-time Streaming** - Cartesia ultra-low latency TTS
- 💬 **Conversation Memory** - Remembers context throughout call

## 🚀 Quick Deployment

### 1. Clone & Deploy
```bash
# Deploy to VPS (run on your VPS)
ssh root@46.224.93.79 'bash -s' < deploy.sh
```

### 2. Configure API Keys
```bash
# Edit production environment
nano /root/app/losteria-ai-receptionist-v2/.env

# Add your keys:
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
OPENAI_API_KEY=your_openai_key
CARTESIA_API_KEY=sk_car_tAmVFvmyCW3dGD6rvGCkuJ
```

### 3. Restart Service
```bash
pm2 restart losteria-ai-receptionist-v2
```

### 4. Update Twilio Webhook
```bash
python3 update_twilio_webhook.py
```

## 🌐 Production URLs

- **Service**: https://adaphone-v2.mindgen.app
- **Test Interface**: https://adaphone-v2.mindgen.app/
- **API Status**: https://adaphone-v2.mindgen.app/api/status
- **Health Check**: https://adaphone-v2.mindgen.app/api/health

## 🧪 Test the System

### Web Interface
Visit https://adaphone-v2.mindgen.app/ to test:
- Real GPT-4o conversation (no demo patterns)
- Dutch language throughout  
- Complete menu knowledge
- Conversation memory

### Phone Testing
Call your Twilio number to test:
- Direct Dutch greeting from Sofia
- Intelligent takeaway conversation
- Professional transfer with hold music

## 🔧 Technical Stack

### Core Technology
- **FastAPI** - Async web framework
- **GPT-4o** - Conversational AI with memory
- **Cartesia TTS** - Ultra-low latency voice synthesis  
- **Twilio Media Streams** - Real-time audio
- **WebSockets** - Bidirectional communication

### Architecture  
```
Phone Call → Twilio → WebSocket → GPT-4o → Cartesia → Audio Stream
```

### Call Flow (v2)
```
Dutch Greeting → Takeaway Conversation (GPT-4o) → Transfer with Hold Music
```

## 📊 Monitoring

### Service Status
```bash
pm2 status
pm2 logs losteria-ai-receptionist-v2
curl https://adaphone-v2.mindgen.app/api/health
```

### Conversation Testing
```bash
# Test GPT-4o memory
python3 test_conversation_memory.py

# Verify Dutch default
python3 test_dutch_default.py

# Test hold music
python3 test_hold_music.py
```

## ⚙️ Configuration

### Restaurant Settings
- **Phone**: +32 56 25 63 83 (L'Osteria Deerlijk)
- **Menu API**: https://ada.mindgen.app/api/v1/menu  
- **Opening Hours**: Built into GPT-4o context
- **Language**: Dutch (nl) by default

### API Endpoints
- `POST /api/voice/webhook` - Twilio voice webhook
- `POST /api/chat` - GPT-4o conversation API
- `GET /api/status` - Service status with features
- `WebSocket /ws/media/{call_sid}` - Real-time audio

## 🚀 CI/CD Pipeline

### Automatic Deployment
GitHub Actions triggers on push to `main`:
1. Deploy to VPS 46.224.93.79
2. Update nginx configuration  
3. Get SSL certificate
4. Restart PM2 service
5. Health check validation

### Manual Override
```bash
# Force deployment
ssh root@46.224.93.79 'bash -s' < deploy.sh

# Update webhook
python3 update_twilio_webhook.py
```

## 🛠️ Development

### Local Testing
```bash
# Start development server
python3 main.py
# → http://localhost:5010

# Test conversation flow
curl -X POST http://localhost:5010/api/chat \
  -d "message=Hallo Sofia&session_id=test123"
```

### Key Files
- `main.py` - FastAPI application with GPT-4o integration
- `test_interface.html` - Real GPT-4o conversation tester
- `ecosystem.config.js` - PM2 production configuration
- `deploy.sh` - VPS deployment script
- `.github/workflows/deploy.yml` - CI/CD pipeline

## 🎯 Production Checklist

- ✅ GPT-4o with conversation memory
- ✅ Dutch language default throughout
- ✅ Complete L'Osteria menu integration
- ✅ Professional hold music + transfer
- ✅ SSL certificate (Let's Encrypt)
- ✅ PM2 process management
- ✅ nginx reverse proxy
- ✅ GitHub Actions deployment
- ✅ Health monitoring endpoints
- ✅ Twilio webhook configuration

## 📞 L'Osteria Deerlijk

**Restaurant Details (Built into AI Context):**
- Address: Stationsstraat 232, 8540 Deerlijk, België
- Phone: +32 56 25 63 83
- Family: Bombini since 1964
- Specialties: Fresh handmade pasta, Napoletan pizza
- Hours: Tue-Sun (Closed Mondays)

Ready for production! 🇳🇱✨