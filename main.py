import logging
import asyncio
from utils.criteria_buy import fetch_ohlcv, calculate_indicators, check_conditions_needed, check_conditions_sufficient
from utils.binance_api import search_tokens
from utils.database import save_needed_tokens, load_needed_tokens
from utils.telegram_bot import send_message
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID



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
    """
    Hàm kiểm tra điều kiện cần hằng ngày và lưu các token đạt điều kiện.
    """
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
            await send_message(message)
        else:
            logging.info("Không có token nào đạt điều kiện cần.")

    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra điều kiện cần: {e}")


async def hourly_check():
    """
    Hàm kiểm tra điều kiện đủ mỗi giờ cho các token đã đạt điều kiện cần.
    """
    global needed_tokens
    logging.info("Bắt đầu kiểm tra điều kiện đủ mỗi giờ...")
    try:
        # Tải danh sách token đạt điều kiện cần từ cơ sở dữ liệu hoặc file
        needed_tokens = load_needed_tokens()
        matched_tokens = []

        for symbol in needed_tokens:
            df = fetch_ohlcv(symbol, interval="1d", limit=100)
            if df.empty:
                logging.warning(f"Không có dữ liệu cho {symbol}.")
                continue

            indicators = calculate_indicators(df)
            if check_conditions_sufficient(df, indicators, symbol):
                matched_tokens.append(symbol)

        if matched_tokens:
            message = f"Token {', '.join(matched_tokens)} khớp điều kiện đủ"
            await send_message(message)
        else:
            logging.info("Không có token nào đạt điều kiện đủ.")

    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra điều kiện đủ: {e}")

# Wrapper để chạy các hàm async với thư viện schedule
def run_async_job(coroutine_function):
    asyncio.run(coroutine_function())

# if __name__ == "__main__":
#     logging.info("Chương trình bắt đầu.")

#     try:
#         # Kiểm tra hàng ngày vào 00:00 và 12:00
#         schedule.every().day.at("00:00").do(run_async_job, daily_check)
#         schedule.every().day.at("12:00").do(run_async_job, daily_check)

#         # Kiểm tra mỗi giờ
#         schedule.every().hour.do(run_async_job, hourly_check)

#         logging.info("Bắt đầu vòng lặp lịch trình.")
#         while True:
#             schedule.run_pending()
#             time.sleep(1)

#     except Exception as e:
#         logging.error(f"Lỗi nghiêm trọng: {e}")

if __name__ == "__main__":
    logging.info("Chương trình bắt đầu.")

    try:
        # Chạy kiểm tra daily_check một lần để test
        logging.info("Chạy kiểm tra daily_check để test...")
        asyncio.run(daily_check())

        # Chạy kiểm tra hourly_check một lần để test
        logging.info("Chạy kiểm tra hourly_check để test...")
        asyncio.run(hourly_check())

        logging.info("Hoàn tất kiểm tra các hàm.")

    except Exception as e:
        logging.error(f"Lỗi nghiêm trọng: {e}")

