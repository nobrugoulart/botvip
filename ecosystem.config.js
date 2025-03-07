module.exports = {
  apps: [
    {
      name: 'telegram-bot',
      script: 'bot.py',
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'web-panel',
      script: 'web_panel.py',
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
}