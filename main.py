import logging
import asyncio
import schedule
import time
from utils.criteria_buy import fetch_ohlcv, calculate_indicators, check_conditions_needed, check_conditions_sufficient
from utils.binance_api import search_tokens
from utils.database import save_needed_tokens, load_needed_tokens
from utils.telegram_bot import send_message
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from datetime import datetime

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Danh sách token đạt điều kiện cần
needed_tokens = []

async def daily_check():

    global needed_tokens
    logging.info("Bắt đầu kiểm tra điều kiện cần hằng ngày...")
    try:
        tokens = search_tokens(lambda token: token["symbol"].endswith("USDT"))
        matched_tokens = []

        for token in tokens:
            symbol = token["symbol"]
            df = fetch_ohlcv(symbol, interval="1d", limit=100)
            if df.empty:
                logging.warning(f"Không có dữ liệu cho {symbol}.")
                continue

            indicators = calculate_indicators(df)
            if check_conditions_needed(df, indicators):
                matched_tokens.append(symbol)

        # Lưu danh sách token đạt điều kiện cần
        needed_tokens = matched_tokens
        save_needed_tokens(matched_tokens)  # Lưu vào cơ sở dữ liệu hoặc file

        if matched_tokens:
            message = f"Danh sách token đạt điều kiện cần: {', '.join(matched_tokens)}"
        else:
            message = "Không có token nào đạt điều kiện cần."

        await send_message(message)

    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra điều kiện cần: {e}")

async def hourly_check():

    global needed_tokens
    logging.info("Bắt đầu kiểm tra điều kiện đủ mỗi giờ...")
    try:
        # Tải danh sách token đạt điều kiện cần từ cơ sở dữ liệu hoặc file
        needed_tokens = load_needed_tokens()
        matched_tokens = []
        failed_tokens = []

        for symbol in needed_tokens:
            df = fetch_ohlcv(symbol, interval="4h", limit=100)
            if df.empty:
                logging.warning(f"Không có dữ liệu cho {symbol}.")
                failed_tokens.append(symbol)
                continue

            indicators = calculate_indicators(df)
            if check_conditions_sufficient(df, indicators, symbol):
                matched_tokens.append(symbol)

        if matched_tokens:
            message = f"Token {', '.join(matched_tokens)} khớp điều kiện đủ"
        else:
            current_time = datetime.now().strftime("%H:%M")
            message = f"{current_time} Không có token đạt điều kiện đủ"

        if failed_tokens:
            logging.warning(f"Các token không thể kiểm tra đủ điều kiện: {', '.join(failed_tokens)}")

        await send_message(message)

    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra điều kiện đủ: {e}")

def run_async_job(coroutine_function):
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(coroutine_function())

if __name__ == "__main__":
    logging.info("Chương trình bắt đầu.")

    try:
        # Tạo vòng lặp sự kiện lâu dài
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Đăng ký lịch trình
        #schedule.every().day.at("21:57").do(run_async_job, daily_check)
        schedule.every().day.at("07:00").do(run_async_job, daily_check)
        schedule.every().hour.do(run_async_job, hourly_check)

        logging.info("Bắt đầu vòng lặp lịch trình.")
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as e:
        logging.error(f"Lỗi nghiêm trọng: {e}")



