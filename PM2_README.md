# Executando o Bot VIP com PM2

Este guia explica como usar o PM2 para gerenciar o Bot VIP e o Painel Web como processos em segundo plano.

## Pré-requisitos

- Node.js e npm instalados
- PM2 instalado globalmente (`npm install -g pm2`)
- Python 3.7 ou superior
- Todas as dependências do projeto instaladas

## Instalação do PM2

Se você ainda não tem o PM2 instalado, execute:

```bash
npm install -g pm2
```

## Executando o Bot VIP com PM2

1. Navegue até o diretório do projeto:

```bash
cd caminho/para/botvip
```

2. Inicie os serviços usando o arquivo de configuração do PM2:

```bash
pm2 start ecosystem.config.js
```

Isso iniciará tanto o bot do Telegram quanto o painel web como processos separados.

## Comandos úteis do PM2

- **Verificar status dos processos**:
  ```bash
  pm2 status
  ```

- **Visualizar logs**:
  ```bash
  pm2 logs                # Todos os logs
  pm2 logs telegram-bot   # Apenas logs do bot
  pm2 logs web-panel      # Apenas logs do painel web
  ```

- **Reiniciar processos**:
  ```bash
  pm2 restart all         # Reiniciar todos os processos
  pm2 restart telegram-bot # Reiniciar apenas o bot
  pm2 restart web-panel   # Reiniciar apenas o painel web
  ```

- **Parar processos**:
  ```bash
  pm2 stop all            # Parar todos os processos
  pm2 stop telegram-bot   # Parar apenas o bot
  pm2 stop web-panel      # Parar apenas o painel web
  ```

- **Configurar inicialização automática** (para que os processos iniciem automaticamente quando o servidor for reiniciado):
  ```bash
  pm2 startup            # Gera o comando para configurar o startup
  pm2 save               # Salva a configuração atual
  ```

## Estrutura do arquivo ecosystem.config.js

O arquivo `ecosystem.config.js` contém a configuração para ambos os processos:

```javascript
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
```

## Solução de problemas

Se encontrar problemas ao executar os processos com PM2:

1. Verifique se todas as dependências estão instaladas:
   ```bash
   pip install -r requirements.txt
   ```

2. Certifique-se de que o arquivo `.env` está configurado corretamente com todas as variáveis necessárias.

3. Verifique os logs para identificar erros específicos:
   ```bash
   pm2 logs
   ```

4. Se necessário, execute os scripts manualmente para verificar se há erros:
   ```bash
   python bot.py
   python web_panel.py
   ```