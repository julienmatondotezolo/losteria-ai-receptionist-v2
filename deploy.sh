#!/bin/bash
# Deployment script for L'Osteria AI Receptionist v2

set -e

echo "🚀 Deploying L'Osteria AI Receptionist v2..."

VPS_HOST="root@46.224.93.79"
VPS_PATH="/root/app/adaphone-v2"
VPS_PASSWORD="9rK2mX5vLqW8nJ4zB1dP"

# Upload files to VPS
echo "📤 Uploading files to VPS..."
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no -r . $VPS_HOST:$VPS_PATH/

# Install dependencies and restart service
echo "📦 Installing dependencies on VPS..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_HOST << EOF
cd $VPS_PATH

# Install Python dependencies
pip3 install -r requirements.txt

# Stop existing service if running
pm2 delete adaphone-v2 2>/dev/null || true

# Start new service
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

echo "✅ Service deployed successfully!"
pm2 status
EOF

echo "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Get Groq API key: https://console.groq.com/"
echo "2. Get Cartesia API key: https://cartesia.ai/"
echo "3. Update ecosystem.config.js with real API keys"
echo "4. Configure nginx for adaphone-v2.mindgen.app"
echo "5. Test with: curl https://adaphone-v2.mindgen.app/api/health"
echo ""
echo "🔗 Service URL: https://adaphone-v2.mindgen.app"
echo "📊 Status: https://adaphone-v2.mindgen.app/api/status"