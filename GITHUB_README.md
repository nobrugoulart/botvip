# Bot VIP - Telegram Bot com Pagamentos PIX via MercadoPago

Um bot para Telegram que gerencia acesso VIP a grupos através de pagamentos PIX processados pelo MercadoPago.

## Funcionalidades

- Geração de pagamentos PIX via MercadoPago
- Verificação automática de status de pagamento
- Gerenciamento de acesso a grupos VIP
- Painel web administrativo
- Notificações automáticas para usuários
- Estatísticas de pagamentos e usuários

## Requisitos

- Python 3.7 ou superior
- Conta no Telegram
- Conta no MercadoPago
- Token de acesso do MercadoPago
- Token de bot do Telegram

## Instalação Rápida (Ubuntu)

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/botvip.git
   cd botvip
   ```

2. Execute o script de instalação:
   ```bash
   chmod +x install_ubuntu.sh
   ./install_ubuntu.sh
   ```

3. Configure suas credenciais no arquivo `.env` criado pelo script de instalação.

4. Reinicie o serviço:
   ```bash
   sudo systemctl restart botvip
   ```

## Instalação Manual

1. Clone este repositório ou baixe os arquivos

2. Instale as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente em um arquivo `.env`:
   ```
   TELEGRAM_TOKEN=seu_token_do_telegram
   MERCADOPAGO_ACCESS_TOKEN=seu_token_do_mercadopago
   VIP_GROUP_ID=id_do_grupo_vip
   ADMIN_USER_ID=seu_id_de_usuario
   PAYMENT_AMOUNT=29.90
   ```

4. Execute o bot:
   ```bash
   python run.py
   ```

## Painel Administrativo

O sistema inclui um painel web administrativo acessível em `http://seu-servidor:5000` que permite:

- Visualizar todos os usuários e seus status
- Gerenciar pagamentos
- Configurar parâmetros do sistema
- Visualizar estatísticas

## Comandos do Bot

- `/start` - Inicia o bot e exibe informações básicas
- `/ajuda` ou `/help` - Mostra a lista de comandos disponíveis
- `/pagar` - Gera um pagamento PIX
- `/status` - Verifica o status do seu pagamento
- `/perfil` - Exibe informações do seu perfil
- `/admin` - Comandos administrativos (apenas para admins)

## Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.