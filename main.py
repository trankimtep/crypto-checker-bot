import logging
import asyncio
from datetime import datetime
from telegram import Bot
from utils.binance_api import search_tokens
from utils.alert_checker import check_conditions
from utils.database import init_db
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from utils.criteria_buy import check_conditions_needed, check_conditions_sufficient, fetch_ohlcv
import schedule
import time
import asyncio

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Khởi tạo bot Telegram
bot = Bot(token=TELEGRAM_TOKEN)

# Danh sách token đạt điều kiện cần
needed_tokens = []

# Hàm gửi tin nhắn qua Telegram
async def send_message(message):
    logging.info("Hàm send_message được gọi.")
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f"Đã gửi tin nhắn: {message}")
    except Exception as e:
        logging.error(f"Lỗi khi gửi tin nhắn: {e}")

# Hàm kiểm tra điều kiện cần và lưu danh sách token
async def check_needed_conditions():
    global needed_tokens
    logging.info("Bắt đầu kiểm tra điều kiện cần...")
    try:
        # Lọc các token có symbol kết thúc bằng "USDT"
        tokens = search_tokens(lambda token: token["symbol"].endswith("USDT") and 
                                              check_conditions_needed(fetch_ohlcv(token["symbol"], "1d", 100)))
        needed_tokens = [t["symbol"] for t in tokens]
        if needed_tokens:
            message = f"Danh sách token đạt điều kiện cần: {', '.join(needed_tokens)}"
            await send_message(message)
        else:
            logging.info("Không tìm thấy token nào đạt điều kiện cần.")
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra điều kiện cần: {e}")


# Hàm kiểm tra điều kiện đủ cho các token trong danh sách
async def check_sufficient_conditions():
    logging.info("Bắt đầu kiểm tra điều kiện đủ...")
    try:
        for symbol in needed_tokens:
            df = fetch_ohlcv(symbol, interval="1d", limit=100)
            if df.empty:
                logging.warning(f"Không có dữ liệu cho {symbol}.")
                continue
            if check_conditions_sufficient(df, symbol):
                message = f"Token {symbol} đạt điều kiện đủ!"
                await send_message(message)
            else:
                logging.info(f"Token {symbol} không đạt điều kiện đủ.")
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra điều kiện đủ: {e}")

# Hàm chạy mỗi ngày để kiểm tra điều kiện cần
async def daily_check():
    now = datetime.now()
    #if now.hour == 0:  # Thực hiện vào 00:00 mỗi ngày
    await check_needed_conditions()

# Hàm chạy mỗi giờ để kiểm tra điều kiện đủ
async def hourly_check():
    await check_sufficient_conditions()

# Hàm chính để chạy bot
async def run_bot():
    logging.info("Hàm run_bot được gọi.")
    await daily_check()
    await hourly_check()

def run_async_job(coroutine_function):
    """
    Wrapper để chạy coroutine (async function) trong schedule.
    :param coroutine_function: Coroutine cần chạy.
    """
    asyncio.run(coroutine_function())

if __name__ == "__main__":
    logging.info("Chương trình bắt đầu.")
    try:
        init_db()
        logging.info("Khởi tạo cơ sở dữ liệu thành công.")
    except Exception as e:
        logging.error(f"Lỗi khi khởi tạo cơ sở dữ liệu: {e}")

    # Lịch trình chạy
    logging.info("Thiết lập lịch trình chạy bot.")
    schedule.every().day.at("21:12").do(run_async_job, daily_check)
    schedule.every().day.at("12:00").do(run_async_job, daily_check) 
    schedule.every().hour.do(hourly_check)           # Chạy điều kiện đủ mỗi giờ

    # Vòng lặp thực thi lịch trình
    logging.info("Bắt đầu vòng lặp lịch trình.")
    while True:
        schedule.run_pending()
        time.sleep(1)



