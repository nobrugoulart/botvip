import os
import logging
import sqlite3
from telegram import Bot
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '7718362919:AAEnz1G99JaN295evqwQUKZ-YMon9wHhJ8M')

# Initialize bot
bot = Bot(token=TELEGRAM_TOKEN)

async def notify_vip_access_granted(user_id, expiry_date=None):
    """
    Send a notification to a user when VIP access is granted.
    
    Args:
        user_id (int): The Telegram user ID to notify
        expiry_date (datetime, optional): The expiry date of the VIP access
    """
    try:
        # Get VIP group ID from settings
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = 'VIP_GROUP_ID'")
        result = cursor.fetchone()
        vip_group_id = result[0] if result else None
        
        conn.close()
        
        # Create invite link
        if vip_group_id:
            invite_link = await bot.create_chat_invite_link(
                chat_id=vip_group_id,
                member_limit=1,
                expire_date=datetime.now().replace(day=datetime.now().day + 1)  # Link expires in 1 day
            )
            
            # Format expiry date message
            expiry_msg = ""
            if expiry_date:
                expiry_msg = f"\nSeu acesso VIP é válido até {expiry_date.strftime('%d/%m/%Y')}"
            
            # Send notification with invite link
            await bot.send_message(
                chat_id=user_id,
                text=f"🎉 *Parabéns! Seu acesso VIP foi ativado!* 🎉\n\n"
                     f"Você agora tem acesso ao nosso grupo exclusivo{expiry_msg}\n\n"
                     f"Clique no link abaixo para entrar no grupo VIP:\n"
                     f"{invite_link.invite_link}",
                parse_mode='Markdown'
            )
            logger.info(f"VIP access notification sent to user {user_id}")
        else:
            # Send notification without invite link
            await bot.send_message(
                chat_id=user_id,
                text=f"🎉 *Parabéns! Seu acesso VIP foi ativado!* 🎉\n\n"
                     f"Seu status VIP foi atualizado com sucesso.",
                parse_mode='Markdown'
            )
            logger.warning(f"VIP access notification sent to user {user_id} without group link (VIP_GROUP_ID not found)")
    except Exception as e:
        logger.error(f"Error sending VIP access notification to user {user_id}: {e}")

async def notify_vip_access_revoked(user_id):
    """
    Send a notification to a user when VIP access is revoked.
    
    Args:
        user_id (int): The Telegram user ID to notify
    """
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"⚠️ *Aviso: Seu acesso VIP foi revogado* ⚠️\n\n"
                 f"Seu acesso ao grupo VIP foi encerrado.\n\n"
                 f"Para renovar seu acesso, use o comando /pagar no bot.",
            parse_mode='Markdown'
        )
        logger.info(f"VIP access revocation notification sent to user {user_id}")
    except Exception as e:
        logger.error(f"Error sending VIP access revocation notification to user {user_id}: {e}")

async def notify_payment_received(user_id, payment_id, amount):
    """
    Send a notification to a user when a payment is received.
    
    Args:
        user_id (int): The Telegram user ID to notify
        payment_id (str): The payment ID
        amount (float): The payment amount
    """
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"💰 *Pagamento Recebido!* 💰\n\n"
                 f"Recebemos seu pagamento de R$ {amount:.2f}\n"
                 f"ID do Pagamento: {payment_id}\n\n"
                 f"Seu acesso VIP está sendo processado e será ativado em breve.",
            parse_mode='Markdown'
        )
        logger.info(f"Payment received notification sent to user {user_id} for payment {payment_id}")
    except Exception as e:
        logger.error(f"Error sending payment notification to user {user_id}: {e}")