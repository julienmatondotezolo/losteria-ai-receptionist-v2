module.exports = {
  apps: [{
    name: 'losteria-ai-receptionist-v2',
    script: 'python3',
    args: 'main.py',
    cwd: '/root/app/losteria-ai-receptionist-v2',
    interpreter: 'none',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: 5010,
      PYTHONPATH: '/root/app/losteria-ai-receptionist-v2',
      RESTAURANT_PHONE: '+32562563983'
    },
    error_file: '/root/logs/losteria-ai-v2.err.log',
    out_file: '/root/logs/losteria-ai-v2.out.log', 
    log_file: '/root/logs/losteria-ai-v2.combined.log',
    time: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
};