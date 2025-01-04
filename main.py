import logging
import asyncio
from telegram import Bot
from utils.binance_api import search_tokens
from utils.alert_checker import check_conditions
from utils.database import init_db
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from utils.criteria_buy import token_meets_criteria

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Ghi log vào file bot.log
        logging.StreamHandler()         # Hiển thị log trên terminal
    ]
)

# Khởi tạo bot Telegram
bot = Bot(token=TELEGRAM_TOKEN)

# Hàm gửi tin nhắn qua Telegram
async def send_message(message):
    logging.info("Hàm send_message được gọi.")
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f"Đã gửi tin nhắn: {message}")
    except Exception as e:
        logging.error(f"Lỗi khi gửi tin nhắn: {e}")

# Hàm xác định tiêu chí tìm kiếm token
def criteria(token):
    """
    Kiểm tra token có thỏa mãn tiêu chí mua hay không.
    """
    return token_meets_criteria(token)

# Hàm chính để chạy bot
async def run_bot():
    logging.info("Hàm run_bot được gọi.")
    # Tìm kiếm các token phù hợp tiêu chí
    logging.info("Bắt đầu tìm kiếm token...")
    try:
        tokens = search_tokens(criteria)
        if tokens:
            message = f"Tìm thấy các token: {', '.join([t['symbol'] for t in tokens])}"
            await send_message(message)
            logging.info("Hoàn thành tìm kiếm token.")
        else:
            logging.info("Không tìm thấy token phù hợp.")
    except Exception as e:
        logging.error(f"Lỗi khi tìm kiếm token: {e}")

    # Kiểm tra các token đã mua
    logging.info("Bắt đầu kiểm tra token đã mua...")
    try:
        alerts = check_conditions()
        for alert in alerts:
            await send_message(alert)
        logging.info("Hoàn thành kiểm tra token.")
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra token: {e}")

# Hàm khởi chạy toàn bộ bot
if __name__ == "__main__":
    logging.info("Chương trình bắt đầu.")
    # Khởi tạo cơ sở dữ liệu (nếu chưa có)
    try:
        init_db()
        logging.info("Khởi tạo cơ sở dữ liệu thành công.")
    except Exception as e:
        logging.error(f"Lỗi khi khởi tạo cơ sở dữ liệu: {e}")

    # Chạy hàm run_bot trực tiếp để kiểm tra
    logging.info("Chạy hàm run_bot để kiểm tra các chức năng.")
    asyncio.run(run_bot())
