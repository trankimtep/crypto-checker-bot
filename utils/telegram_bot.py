import logging
from telegram import Bot
from config import TELEGRAM_TOKEN

# Khởi tạo bot
bot = Bot(token=TELEGRAM_TOKEN)

async def send_message(chat_id, message):
    """
    Gửi thông báo qua Telegram.
    """

    try:
        await bot.send_message(chat_id=chat_id, text=message)
        logging.info(f"Gửi thông báo thành công đến {chat_id}: {message}")
    except Exception as e:
        logging.error(f"Lỗi khi gửi thông báo đến {chat_id}: {e}")
