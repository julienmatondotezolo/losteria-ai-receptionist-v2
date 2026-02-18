#!/bin/bash

# 🚀 L'Osteria AI Receptionist v2 - VPS Deployment Script
# Run this on your VPS: ssh root@46.224.93.79 'bash -s' < deploy.sh

set -e

echo "🚀 Starting deployment of L'Osteria AI Receptionist v2..."

# Create logs directory
mkdir -p /root/logs

# Navigate to project directory
cd /root/app/losteria-ai-receptionist-v2 || {
    echo "📁 Creating project directory..."
    mkdir -p /root/app/losteria-ai-receptionist-v2
    cd /root/app/losteria-ai-receptionist-v2
    git clone https://github.com/julienmatondotezolo/losteria-ai-receptionist-v2.git .
}

# Pull latest changes
echo "📦 Pulling latest code..."
git fetch origin
git reset --hard origin/main

# Show recent commits
echo "📋 Recent changes:"
git log --oneline -3

# Create .env file with production settings
echo "⚙️ Configuring environment..."
cat > .env << 'EOF'
# Production Configuration
NODE_ENV=production
PORT=5010

# API Keys - UPDATE WITH REAL VALUES
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
OPENAI_API_KEY=your_openai_api_key
CARTESIA_API_KEY=sk_car_tAmVFvmyCW3dGD6rvGCkuJ

# Restaurant Configuration
RESTAURANT_PHONE=+32562563983
EOF

echo "⚠️  IMPORTANT: Update .env file with real API keys!"

# Install/update Python dependencies
echo "📦 Installing dependencies..."
python3 -m pip install -r requirements.txt

# Stop existing service
echo "🛑 Stopping existing services..."
pkill -f "python.*main.py" || true
pm2 delete losteria-ai-v2 || true
pm2 delete adaphone-v2 || true
sleep 3

# Start new service with PM2
echo "🚀 Starting new service..."
pm2 start ecosystem.config.js
pm2 save

# Configure nginx
echo "🌐 Configuring nginx..."
cat > /etc/nginx/sites-available/adaphone-v2.mindgen.app << 'EOF'
server {
    listen 80;
    server_name adaphone-v2.mindgen.app;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name adaphone-v2.mindgen.app;

    # SSL configuration will be added by certbot
    
    location / {
        proxy_pass http://localhost:5010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    location /ws/ {
        proxy_pass http://localhost:5010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/adaphone-v2.mindgen.app /etc/nginx/sites-enabled/
nginx -t

# Get SSL certificate
echo "🔐 Getting SSL certificate..."
certbot certonly --nginx -d adaphone-v2.mindgen.app --non-interactive --agree-tos --email emji@mindgen.be || {
    echo "⚠️ SSL certificate setup failed - continuing without HTTPS for now"
    systemctl reload nginx
}

systemctl reload nginx

# Check deployment
echo "🔍 Checking deployment..."
sleep 10

curl -f http://localhost:5010/api/health || {
    echo "❌ Health check failed - checking logs:"
    pm2 logs losteria-ai-receptionist-v2 --lines 20
    exit 1
}

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Service URLs:"
echo "   - Health: http://localhost:5010/api/health"  
echo "   - Status: https://adaphone-v2.mindgen.app/api/status"
echo "   - Test Interface: https://adaphone-v2.mindgen.app/"
echo ""
echo "📊 Service Status:"
pm2 status

echo ""
echo "⚙️  Next Steps:"
echo "   1. Update .env file with real API keys"
echo "   2. Restart PM2: pm2 restart losteria-ai-receptionist-v2"
echo "   3. Update Twilio webhook to: https://adaphone-v2.mindgen.app/api/voice/webhook"
echo ""