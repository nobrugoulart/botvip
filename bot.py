import os
import logging
import sqlite3
import base64
import io
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, CallbackContext
import mercadopago

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '7718362919:AAEnz1G99JaN295evqwQUKZ-YMon9wHhJ8M')
MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN', 'APP_USR-4358712787761609-101612-9323686cdb55de2edc92bd6834420501-1001556032')
VIP_GROUP_ID = os.environ.get('VIP_GROUP_ID', '-1002370145572')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID', '6798939401')
PAYMENT_AMOUNT = float(os.environ.get('PAYMENT_AMOUNT', '1'))  # Default payment amount in BRL

# Initialize MercadoPago SDK
mp = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)

# Database setup
def setup_database():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        payment_id TEXT,
        payment_status TEXT,
        payment_date TIMESTAMP,
        expiry_date TIMESTAMP,
        is_vip BOOLEAN DEFAULT 0
    )
    ''')
    
    # Create payments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        payment_id TEXT PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        status TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    user_id = user.id
    
    # Check if user exists in database
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT is_vip, expiry_date FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    
    if user_data:
        is_vip = user_data[0]
        expiry_date = user_data[1]
        
        if is_vip:
            expiry_msg = ""
            if expiry_date:
                expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S.%f') if isinstance(expiry_date, str) else expiry_date
                expiry_msg = f"\n🗓️ Seu acesso VIP é válido até {expiry_date_obj.strftime('%d/%m/%Y')}"
            
            keyboard = [
                [InlineKeyboardButton("🔑 Acessar Grupo VIP", callback_data="get_vip_link")],
                [InlineKeyboardButton("💳 Renovar Acesso", callback_data="renew_vip")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_html(
                f"Olá, {user.mention_html()}! 👋\n\n"
                f"Bem-vindo de volta ao Bot VIP! Você já possui acesso VIP ativo.{expiry_msg}\n\n"
                f"Use os botões abaixo para acessar o grupo ou renovar seu acesso.",
                reply_markup=reply_markup
            )
        else:
            keyboard = [
                [InlineKeyboardButton("💰 Fazer Pagamento", callback_data="make_payment")],
                [InlineKeyboardButton("ℹ️ Informações", callback_data="show_info")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_html(
                f"Olá, {user.mention_html()}! 👋\n\n"
                f"Bem-vindo ao Bot VIP! Aqui você pode fazer pagamentos via PIX para ter acesso ao nosso grupo exclusivo.\n\n"
                f"Use os botões abaixo ou os seguintes comandos:\n"
                f"- /pagar para gerar um pagamento PIX\n"
                f"- /status para verificar o status do seu pagamento\n"
                f"- /perfil para ver suas informações\n"
                f"- /ajuda para ver todos os comandos disponíveis",
                reply_markup=reply_markup
            )
    else:
        # New user
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, user.username, user.first_name)
        )
        conn.commit()
        
        keyboard = [
            [InlineKeyboardButton("💰 Fazer Pagamento", callback_data="make_payment")],
            [InlineKeyboardButton("ℹ️ Informações", callback_data="show_info")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(
            f"Olá, {user.mention_html()}! 👋\n\n"
            f"Bem-vindo ao Bot VIP! Aqui você pode fazer pagamentos via PIX para ter acesso ao nosso grupo exclusivo.\n\n"
            f"Use os botões abaixo ou os seguintes comandos:\n"
            f"- /pagar para gerar um pagamento PIX\n"
            f"- /status para verificar o status do seu pagamento\n"
            f"- /perfil para ver suas informações\n"
            f"- /ajuda para ver todos os comandos disponíveis",
            reply_markup=reply_markup
        )
    
    conn.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Comandos disponíveis:\n\n"
        "/start - Iniciar o bot\n"
        "/pagar - Gerar um pagamento PIX\n"
        "/status - Verificar status do pagamento\n"
        "/perfil - Ver suas informações de conta\n"
        "/ajuda - Mostrar esta mensagem de ajuda\n\n"
        "Para suporte, entre em contato com o administrador."
    )

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile information."""
    user = update.effective_user
    user_id = user.id
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT is_vip, expiry_date, payment_status, payment_date FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        await update.message.reply_text("Não foi possível encontrar suas informações. Por favor, use /start para registrar-se.")
        conn.close()
        return
    
    is_vip = user_data[0]
    expiry_date = user_data[1]
    payment_status = user_data[2] or "Nenhum"
    payment_date = user_data[3]
    
    # Get payment history
    cursor.execute(
        "SELECT payment_id, amount, status, created_at FROM payments WHERE user_id = ? ORDER BY created_at DESC LIMIT 3", 
        (user_id,)
    )
    payments = cursor.fetchall()
    
    # Format profile message
    profile_message = f"👤 *Perfil do Usuário* 👤\n\n"
    profile_message += f"ID: `{user_id}`\n"
    profile_message += f"Nome: {user.first_name}\n"
    if user.username:
        profile_message += f"Username: @{user.username}\n"
    
    profile_message += f"\n📊 *Status da Conta* 📊\n"
    profile_message += f"Status VIP: {'✅ Ativo' if is_vip else '❌ Inativo'}\n"
    
    if is_vip and expiry_date:
        expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S.%f') if isinstance(expiry_date, str) else expiry_date
        profile_message += f"Expira em: {expiry_date_obj.strftime('%d/%m/%Y')}\n"
    
    profile_message += f"\n💳 *Informações de Pagamento* 💳\n"
    profile_message += f"Último status: {payment_status}\n"
    
    if payment_date:
        payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d %H:%M:%S.%f') if isinstance(payment_date, str) else payment_date
        profile_message += f"Data: {payment_date_obj.strftime('%d/%m/%Y %H:%M')}\n"
    
    if payments:
        profile_message += f"\n📝 *Histórico de Pagamentos* 📝\n"
        for payment in payments:
            payment_id = payment[0]
            amount = payment[1]
            status = payment[2]
            date = payment[3]
            date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f') if isinstance(date, str) else date
            profile_message += f"- {date_obj.strftime('%d/%m/%Y')}: R$ {amount:.2f} ({status})\n"
    
    # Add buttons
    keyboard = []
    if is_vip:
        keyboard.append([InlineKeyboardButton("🔑 Acessar Grupo VIP", callback_data="get_vip_link")])
    else:
        keyboard.append([InlineKeyboardButton("💰 Fazer Pagamento", callback_data="make_payment")])
    
    if payment_status in ["pending", "in_process"]:
        keyboard.append([InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_payment_{user_data[0]}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(profile_message, parse_mode='Markdown', reply_markup=reply_markup)
    conn.close()

async def generate_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a PIX payment."""
    user = update.effective_user
    user_id = user.id
    
    # Check if this is a callback query
    is_callback = update.callback_query is not None
    query = update.callback_query if is_callback else None
    
    # Create payment preference in MercadoPago
    preference_data = {
        "items": [
            {
                "title": "Acesso VIP",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": PAYMENT_AMOUNT
            }
        ],
        "payer": {
            "name": user.first_name,
            "email": f"user_{user_id}@example.com"  # Placeholder email
        },
        "payment_methods": {
            "excluded_payment_methods": [],
            "excluded_payment_types": [
                {"id": "credit_card"},
                {"id": "debit_card"},
                {"id": "ticket"}
            ],
            "installments": 1
        },
        "external_reference": str(user_id),
        "notification_url": "https://your-webhook-url.com/notifications",  # Replace with your webhook URL
    }
    
    preference_response = mp.preference().create(preference_data)
    preference = preference_response["response"]
    
    # Get PIX info
    payment_methods = mp.payment_methods().list_all()
    pix_info = None
    for method in payment_methods["response"]:
        if method["id"] == "pix":
            pix_info = method
            break
    
    # Create payment in MercadoPago
    payment_data = {
        "transaction_amount": PAYMENT_AMOUNT,
        "description": "Acesso VIP",
        "payment_method_id": "pix",
        "payer": {
            "email": f"user_{user_id}@example.com",
            "first_name": user.first_name,
            "identification": {
                "type": "CPF",
                "number": "12345678909"  # This should be replaced with actual data in production
            }
        }
    }
    
    payment_response = mp.payment().create(payment_data)
    payment = payment_response["response"]
    
    # Store payment info in database
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_exists = cursor.fetchone()
    
    current_time = datetime.now()
    
    if not user_exists:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, payment_id, payment_status, payment_date) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, user.username, user.first_name, payment["id"], payment["status"], current_time)
        )
    else:
        cursor.execute(
            "UPDATE users SET payment_id = ?, payment_status = ?, payment_date = ? WHERE user_id = ?",
            (payment["id"], payment["status"], current_time, user_id)
        )
    
    cursor.execute(
        "INSERT INTO payments (payment_id, user_id, amount, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (payment["id"], user_id, PAYMENT_AMOUNT, payment["status"], current_time, current_time)
    )
    
    conn.commit()
    conn.close()
    
    # Create PIX QR code and payment info
    qr_code_base64 = payment["point_of_interaction"]["transaction_data"]["qr_code_base64"]
    qr_code = payment["point_of_interaction"]["transaction_data"]["qr_code"]
    
    # Create payment message
    payment_message = (
        "💰 *Pagamento PIX Gerado* 💰\n\n"
        f"Valor: R$ {PAYMENT_AMOUNT:.2f}\n"
        "Status: ⏳ Aguardando pagamento\n\n"
        "*Instruções:*\n"
        "1. Abra seu app bancário\n"
        "2. Escolha pagar via PIX\n"
        "3. Copie o código abaixo ou escaneie o QR code\n\n"
        f"*Código PIX:*\n`{qr_code}`\n\n"
        "Após o pagamento, clique em 'Verificar Pagamento' para atualizar o status."
    )
    
    # Send payment information to user
    keyboard = [
        [InlineKeyboardButton("Verificar Pagamento", callback_data=f"check_payment_{payment['id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle different update types
    if is_callback:
        await query.edit_message_text(
            payment_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            payment_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # Send QR code image
    qr_code_bytes = base64.b64decode(qr_code_base64)
    qr_code_image = io.BytesIO(qr_code_bytes)
    qr_code_image.name = 'qr_code.png'
    
    if is_callback:
        await query.message.reply_photo(
            qr_code_image,
            caption="QR Code para pagamento PIX"
        )
    else:
        await update.message.reply_photo(
            qr_code_image,
            caption="QR Code para pagamento PIX"
        )

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the status of a payment."""
    user = update.effective_user
    user_id = user.id
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT payment_id, payment_status, is_vip FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data or not user_data[0]:
        await update.message.reply_text(
            "Você ainda não gerou nenhum pagamento. Use /pagar para gerar um pagamento PIX."
        )
        conn.close()
        return
    
    payment_id = user_data[0]
    current_status = user_data[1]
    is_vip = user_data[2]
    
    # Check payment status in MercadoPago
    payment_response = mp.payment().get(payment_id)
    payment = payment_response["response"]
    
    new_status = payment["status"]
    
    # Update status in database if changed
    if new_status != current_status:
        cursor.execute(
            "UPDATE users SET payment_status = ? WHERE user_id = ?",
            (new_status, user_id)
        )
        cursor.execute(
            "UPDATE payments SET status = ?, updated_at = ? WHERE payment_id = ?",
            (new_status, datetime.now(), payment_id)
        )
        conn.commit()
    
    # Grant VIP access if payment is approved
    if new_status == "approved" and not is_vip:
        # Set user as VIP
        cursor.execute(
            "UPDATE users SET is_vip = 1, expiry_date = ? WHERE user_id = ?",
            (datetime.now().replace(month=datetime.now().month + 1), user_id)  # VIP for 1 month
        )
        conn.commit()
        
        # Import and use notification functions
        from notifications import notify_payment_received, notify_vip_access_granted
        
        # Send payment received notification
        await notify_payment_received(user_id, payment_id, PAYMENT_AMOUNT)
        
        # Send VIP access granted notification with expiry date
        await notify_vip_access_granted(user_id, datetime.now().replace(month=datetime.now().month + 1))
        
        # Add user to VIP group
        try:
            # Invite user to the VIP group
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=VIP_GROUP_ID,
                member_limit=1,
                expire_date=datetime.now().replace(day=datetime.now().day + 1)  # Link expires in 1 day
            )
            
            keyboard = [
                [InlineKeyboardButton("Entrar no Grupo VIP", url=invite_link.invite_link)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🎉 *Pagamento Aprovado!* 🎉\n\n"
                "Seu acesso VIP foi ativado com sucesso. Clique no botão abaixo para entrar no grupo exclusivo.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error adding user to VIP group: {e}")
            await update.message.reply_text(
                "Pagamento aprovado, mas houve um erro ao adicionar você ao grupo VIP. Por favor, contate o administrador."
            )
    else:
        status_messages = {
            "pending": "⏳ *Pagamento Pendente* ⏳\n\nAinda não recebemos a confirmação do seu pagamento. Por favor, tente novamente em alguns instantes.",
            "approved": "✅ *Pagamento Aprovado* ✅\n\nVocê já tem acesso ao grupo VIP!",
            "authorized": "⏳ *Pagamento Autorizado* ⏳\n\nSeu pagamento foi autorizado e está sendo processado.",
            "in_process": "⏳ *Pagamento Em Processo* ⏳\n\nSeu pagamento está sendo processado.",
            "in_mediation": "⚠️ *Pagamento Em Mediação* ⚠️\n\nSeu pagamento está em análise. Por favor, contate o administrador.",
            "rejected": "❌ *Pagamento Rejeitado* ❌\n\nSeu pagamento foi rejeitado. Por favor, tente novamente ou contate o administrador.",
            "cancelled": "❌ *Pagamento Cancelado* ❌\n\nSeu pagamento foi cancelado. Use /pagar para gerar um novo pagamento.",
            "refunded": "♻️ *Pagamento Reembolsado* ♻️\n\nSeu pagamento foi reembolsado.",
            "charged_back": "⚠️ *Pagamento Contestado* ⚠️\n\nSeu pagamento foi contestado."
        }
        
        status_message = status_messages.get(new_status, f"Status do pagamento: {new_status}")
        
        keyboard = [
            [InlineKeyboardButton("Verificar Novamente", callback_data=f"check_payment_{payment_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    conn.close()

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "get_vip_link":
        try:
            # Get VIP group ID from settings
            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT value FROM settings WHERE key = 'VIP_GROUP_ID'")
            result = cursor.fetchone()
            vip_group_id = result[0] if result else VIP_GROUP_ID
            
            conn.close()
            
            # Create invite link
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=vip_group_id,
                member_limit=1,
                expire_date=datetime.now().replace(day=datetime.now().day + 1)  # Link expires in 1 day
            )
            
            keyboard = [
                [InlineKeyboardButton("🔑 Entrar no Grupo VIP", url=invite_link.invite_link)],
                [InlineKeyboardButton("🔙 Voltar", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔑 *Acesso ao Grupo VIP* 🔑\n\n"
                "Clique no botão abaixo para entrar no grupo exclusivo.\n\n"
                "Este link é válido por 24 horas e pode ser usado apenas uma vez.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error creating invite link: {e}")
            await query.edit_message_text(
                "Ocorreu um erro ao gerar o link de convite. Por favor, tente novamente mais tarde ou contate o administrador."
            )
    
    elif data == "renew_vip":
        # Redirect to payment generation
        if isinstance(update.callback_query.message, Message):
            await generate_payment(update, context)
        else:
            await query.edit_message_text(
                "💰 *Gerando Pagamento* 💰\n\nPor favor, aguarde...",
                parse_mode='Markdown'
            )
            await generate_payment(update, context)
    
    elif data == "make_payment":
        # Redirect to payment generation
        if isinstance(update.callback_query.message, Message):
            await generate_payment(update, context)
        else:
            await query.edit_message_text(
                "💰 *Gerando Pagamento* 💰\n\nPor favor, aguarde...",
                parse_mode='Markdown'
            )
            await generate_payment(update, context)
    
    elif data == "show_info":
        await query.edit_message_text(
            "ℹ️ *Informações sobre o Bot VIP* ℹ️\n\n"
            "Este bot permite que você faça pagamentos via PIX para ter acesso ao nosso grupo VIP exclusivo.\n\n"
            "*Como funciona:*\n"
            "1. Gere um pagamento usando o comando /pagar\n"
            "2. Escaneie o QR Code ou copie o código PIX\n"
            "3. Realize o pagamento pelo seu aplicativo bancário\n"
            "4. Verifique o status do pagamento usando /status\n"
            "5. Após a confirmação, você receberá um link para entrar no grupo VIP\n\n"
            "*Comandos disponíveis:*\n"
            "/start - Iniciar o bot\n"
            "/pagar - Gerar um pagamento PIX\n"
            "/status - Verificar status do pagamento\n"
            "/perfil - Ver suas informações de conta\n"
            "/ajuda - Mostrar a mensagem de ajuda\n\n"
            "Para suporte, entre em contato com o administrador.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="back_to_main")]])
        )
    
    elif data == "back_to_main":
        # Return to main menu
        await start(update, context)
    
    elif data.startswith("check_payment_"):
        payment_id = data.split("_")[2]
        
        # Check payment status in MercadoPago
        payment_response = mp.payment().get(payment_id)
        payment = payment_response["response"]
        
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT payment_status, is_vip FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            await query.edit_message_text(
                "Erro ao verificar pagamento. Por favor, use /status para verificar o status do seu pagamento."
            )
            conn.close()
            return
        
        current_status = user_data[0]
        is_vip = user_data[1]
        
        new_status = payment["status"]
        
        # Update status in database if changed
        if new_status != current_status:
            cursor.execute(
                "UPDATE users SET payment_status = ? WHERE user_id = ?",
                (new_status, user_id)
            )
            cursor.execute(
                "UPDATE payments SET status = ?, updated_at = ? WHERE payment_id = ?",
                (new_status, datetime.now(), payment_id)
            )
            conn.commit()
        
        # Grant VIP access if payment is approved
        if new_status == "approved" and not is_vip:
            # Set user as VIP
            expiry_date = datetime.now().replace(month=datetime.now().month + 1)  # VIP for 1 month
            cursor.execute(
                "UPDATE users SET is_vip = 1, expiry_date = ? WHERE user_id = ?",
                (expiry_date, user_id)
            )
            conn.commit()
            
            # Add user to VIP group
            try:
                # Invite user to the VIP group
                invite_link = await context.bot.create_chat_invite_link(
                    chat_id=VIP_GROUP_ID,
                    member_limit=1,
                    expire_date=datetime.now().replace(day=datetime.now().day + 1)  # Link expires in 1 day
                )
                
                keyboard = [
                    [InlineKeyboardButton("Entrar no Grupo VIP", url=invite_link.invite_link)]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "🎉 *Pagamento Aprovado!* 🎉\n\n"
                    "Seu acesso VIP foi ativado com sucesso. Clique no botão abaixo para entrar no grupo exclusivo.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
                # Notify user via notifications module
                from notifications import notify_vip_access_granted
                try:
                    await notify_vip_access_granted(user_id, expiry_date)
                except Exception as e:
                    logger.error(f"Error sending VIP access notification: {e}")
                
            except Exception as e:
                logger.error(f"Error adding user to VIP group: {e}")
                await query.edit_message_text(
                    "Pagamento aprovado, mas houve um erro ao adicionar você ao grupo VIP. Por favor, contate o administrador."
                )
        else:
            status_messages = {
                "pending": "⏳ *Pagamento Pendente* ⏳\n\nAinda não recebemos a confirmação do seu pagamento. Por favor, tente novamente em alguns instantes.",
                "approved": "✅ *Pagamento Aprovado* ✅\n\nVocê já tem acesso ao grupo VIP!",
                "authorized": "⏳ *Pagamento Autorizado* ⏳\n\nSeu pagamento foi autorizado e está sendo processado.",
                "in_process": "⏳ *Pagamento Em Processo* ⏳\n\nSeu pagamento está sendo processado.",
                "in_mediation": "⚠️ *Pagamento Em Mediação* ⚠️\n\nSeu pagamento está em análise. Por favor, contate o administrador.",
                "rejected": "❌ *Pagamento Rejeitado* ❌\n\nSeu pagamento foi rejeitado. Por favor, tente novamente ou contate o administrador.",
                "cancelled": "❌ *Pagamento Cancelado* ❌\n\nSeu pagamento foi cancelado. Use /pagar para gerar um novo pagamento.",
                "refunded": "♻️ *Pagamento Reembolsado* ♻️\n\nSeu pagamento foi reembolsado.",
                "charged_back": "⚠️ *Pagamento Contestado* ⚠️\n\nSeu pagamento foi contestado."
            }

# Admin commands
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin statistics."""
    user = update.effective_user
    user_id = user.id
    
    # Check if user is admin
    if str(user_id) != ADMIN_USER_ID:
        await update.message.reply_text("Você não tem permissão para usar este comando.")
        return
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # Get total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Get VIP users
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1")
    vip_users = cursor.fetchone()[0]
    
    # Get total payments
    cursor.execute("SELECT COUNT(*) FROM payments")
    total_payments = cursor.fetchone()[0]
    
    # Get approved payments
    cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'approved'")
    approved_payments = cursor.fetchone()[0]
    
    # Get total revenue
    cursor.execute("SELECT SUM(amount) FROM payments WHERE status = 'approved'")
    total_revenue = cursor.fetchone()[0] or 0
    
    # Get recent payments
    cursor.execute(
        """SELECT u.username, u.first_name, p.amount, p.status, p.updated_at 
        FROM payments p JOIN users u ON p.user_id = u.user_id 
        ORDER BY p.updated_at DESC LIMIT 5"""
    )
    recent_payments = cursor.fetchall()
    
    stats_message = (
        f"📊 *Estatísticas do Bot VIP* 📊\n\n"
        f"👥 Total de Usuários: {total_users}\n"
        f"🌟 Usuários VIP: {vip_users}\n"
        f"💳 Total de Pagamentos: {total_payments}\n"
        f"✅ Pagamentos Aprovados: {approved_payments}\n"
        f"💰 Receita Total: R$ {total_revenue:.2f}\n\n"
        f"📝 *Pagamentos Recentes:*\n"
    )
    
    for payment in recent_payments:
        username = payment[0] or payment[1]  # Use first_name if username is None
        amount = payment[2]
        status = payment[3]
        date = payment[4]
        stats_message += f"- {username}: R$ {amount:.2f} ({status}) - {date}\n"
    
    await update.message.reply_text(stats_message, parse_mode='Markdown')
    conn.close()

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Setup database
    setup_database()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ajuda", help_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("pagar", generate_payment))
    application.add_handler(CommandHandler("status", check_payment_status))
    application.add_handler(CommandHandler("perfil", profile_command))
    application.add_handler(CommandHandler("admin", admin_stats))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()