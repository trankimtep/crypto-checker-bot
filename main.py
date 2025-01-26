import logging
import asyncio
import schedule
import time
from utils.criteria_buy import fetch_ohlcv, calculate_indicators, check_conditions_needed, check_conditions_sufficient
from utils.binance_api import search_tokens
from utils.telegram_bot import send_message
from datetime import datetime
from config import CHANNEL_SURE, CHANNEL_RISKY

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

async def check_certain_channel():
    """
    Kiểm tra điều kiện cần và đủ cho channel "chắc chắn".
    """
    global needed_tokens
    logging.info("Bắt đầu kiểm tra channel chắc chắn...")
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

        if matched_tokens:
            message = f"Danh sách token đạt điều kiện cần: {', '.join(matched_tokens)}"
            logging.info(message)
            await send_message(CHANNEL_SURE, message)
        else:
            await send_message(CHANNEL_SURE, "Không có token nào đạt điều kiện cần.")

    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra channel chắc chắn: {e}")

async def check_certain_channel_sufficient():
    """
    Kiểm tra điều kiện đủ cho channel "chắc chắn".
    """
    global needed_tokens
    logging.info("Bắt đầu kiểm tra điều kiện đủ channel chắc chắn...")
    try:
        matched_tokens = []

        for symbol in needed_tokens:
            df = fetch_ohlcv(symbol, interval="4h", limit=100)
            if df.empty:
                logging.warning(f"Không có dữ liệu cho {symbol}.")
                continue

            indicators = calculate_indicators(df)
            if check_conditions_sufficient(df, indicators, symbol):
                matched_tokens.append(symbol)

        if matched_tokens:
            message = f"Token {', '.join(matched_tokens)} khớp điều kiện đủ"
            await send_message(CHANNEL_SURE, message)
        else:
            current_time = datetime.now().strftime("%H:%M")
            message = f"{current_time} Không có token đạt điều kiện đủ"
            await send_message(CHANNEL_SURE, message)

    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra channel chắc chắn: {e}")

async def check_risky_channel():
    """
    Kiểm tra điều kiện đủ cho tất cả các token cho channel "mạo hiểm".
    """
    logging.info("Bắt đầu kiểm tra channel mạo hiểm...")
    try:
        tokens = search_tokens(lambda token: token["symbol"].endswith("USDT"))
        matched_tokens = []

        for token in tokens:
            symbol = token["symbol"]
            df = fetch_ohlcv(symbol, interval="4h", limit=100)
            if df.empty:
                logging.warning(f"Không có dữ liệu cho {symbol}.")
                continue

            indicators = calculate_indicators(df)
            if check_conditions_sufficient(df, indicators, symbol):
                matched_tokens.append(symbol)

        if matched_tokens:
            message = f" Token {', '.join(matched_tokens)} khớp điều kiện đủ"
            await send_message(CHANNEL_RISKY, message)
        else:
            logging.info("Không có token khớp điều kiện đủ") 
        # else:
        #     current_time = datetime.now().strftime("%H:%M")
        #     message = f" {current_time} Không có token đạt điều kiện đủ"
        #     await send_message(CHANNEL_RISKY, message)

    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra channel mạo hiểm: {e}")

def run_async_job(coroutine_function):
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(coroutine_function())

if __name__ == "__main__":
    logging.info("Chương trình bắt đầu.")

    try:
        # Lịch trình channel chắc chắn
        schedule.every().day.at("00:00").do(run_async_job, check_certain_channel)
        schedule.every().day.at("12:00").do(run_async_job, check_certain_channel)
        #schedule.every(30).minutes.do(run_async_job, check_certain_channel_sufficient)

        # Lịch trình channel mạo hiểm
        schedule.every(30).minutes.do(run_async_job, check_risky_channel)

        logging.info("Bắt đầu vòng lặp lịch trình.")
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception as e:
        logging.error(f"Lỗi nghiêm trọng: {e}")