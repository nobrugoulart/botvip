# Bot VIP - Telegram Bot com Pagamentos PIX via MercadoPago

Este é um bot para Telegram que permite gerenciar acesso a um grupo VIP através de pagamentos PIX processados pelo MercadoPago.

## Funcionalidades

- Geração de pagamentos PIX via MercadoPago
- Verificação automática do status de pagamento
- Concessão automática de acesso ao grupo VIP após confirmação do pagamento
- Painel administrativo com estatísticas de pagamentos e usuários
- Banco de dados SQLite para armazenamento de informações de usuários e pagamentos

## Requisitos

- Python 3.7 ou superior
- Conta no Telegram
- Conta no MercadoPago
- Token de acesso do MercadoPago
- Token de bot do Telegram

## Instalação

1. Clone este repositório ou baixe os arquivos
2. Instale as dependências necessárias:

```bash
pip install python-telegram-bot mercadopago
```

## Configuração

Antes de executar o bot, você precisa configurar as seguintes variáveis de ambiente:

- `TELEGRAM_TOKEN`: Token do seu bot do Telegram (obtido através do @BotFather)
- `MERCADOPAGO_ACCESS_TOKEN`: Token de acesso da sua conta MercadoPago
- `VIP_GROUP_ID`: ID do grupo VIP do Telegram
- `ADMIN_USER_ID`: ID do usuário administrador do bot
- `PAYMENT_AMOUNT`: Valor do pagamento em BRL (padrão: 29.90)

Você pode configurar estas variáveis de ambiente no seu sistema ou criar um arquivo `.env` na raiz do projeto.

### Exemplo de arquivo .env

```
TELEGRAM_TOKEN=seu_token_do_telegram
MERCADOPAGO_ACCESS_TOKEN=seu_token_do_mercadopago
VIP_GROUP_ID=id_do_grupo_vip
ADMIN_USER_ID=seu_id_de_usuario
PAYMENT_AMOUNT=29.90
```

## Executando o Bot

Para iniciar o bot, execute:

```bash
python bot.py
```

## Comandos Disponíveis

- `/start` - Inicia o bot e exibe uma mensagem de boas-vindas
- `/pagar` - Gera um pagamento PIX
- `/status` - Verifica o status do pagamento
- `/ajuda` - Mostra a mensagem de ajuda
- `/admin` - Exibe estatísticas (apenas para administradores)

## Webhook para Notificações

Para receber notificações automáticas do MercadoPago, você precisa configurar um webhook. Substitua a URL em `notification_url` no código por sua URL de webhook.

## Personalização

Você pode personalizar o bot alterando as mensagens, valores e comportamentos no código-fonte conforme necessário.

## Observações

- Em ambiente de produção, substitua os dados de identificação do pagador por dados reais
- Configure corretamente o webhook para receber notificações do MercadoPago
- Certifique-se de que o bot tenha permissões para adicionar membros ao grupo VIP

## Licença

Este projeto está licenciado sob a licença MIT.