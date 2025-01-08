import logging
from telegram import Bot
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

# Khởi tạo bot Telegram
bot = Bot(token=TELEGRAM_TOKEN)

async def send_message(message):
    """
    Gửi tin nhắn qua Telegram.
    :param message: Nội dung tin nhắn.
    """
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f"Đã gửi tin nhắn: {message}")
    except Exception as e:
        logging.error(f"Lỗi khi gửi tin nhắn qua Telegram: {e}")
