module.exports = {
  apps: [{
    name: 'adaphone-v2',
    script: 'uvicorn',
    args: 'main:app --host 0.0.0.0 --port 5010 --workers 1',
    cwd: '/root/app/adaphone-v2',
    interpreter: 'python3',
    env: {
      NODE_ENV: 'production',
      PORT: '5010',
      // Twilio Configuration
      TWILIO_ACCOUNT_SID: 'YOUR_TWILIO_ACCOUNT_SID',
      TWILIO_AUTH_TOKEN: 'd0bfd8af55a682976d4458e18fff3d95', 
      TWILIO_PHONE_NUMBER: '+18287840392',
      // AI Services
      OPENAI_API_KEY: 'your-openai-api-key-here',
      CARTESIA_API_KEY: 'your-cartesia-api-key-here',
      // Restaurant Config
      RESTAURANT_PHONE: '+32_56_25_63_83',
      BOOKING_URL: 'https://l-osteria.be/',
      MENU_API_URL: 'https://ada.mindgen.app/api/v1/menu'
    },
    instances: 1,
    exec_mode: 'fork',
    watch: false,
    max_memory_restart: '500M',
    error_file: '/var/log/pm2/adaphone-v2-error.log',
    out_file: '/var/log/pm2/adaphone-v2-out.log',
    log_file: '/var/log/pm2/adaphone-v2.log',
    time: true
  }]
};