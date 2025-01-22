# utils/binance_api.py

import logging
import pandas as pd
from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_SECRET_KEY

# Khởi tạo client
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_SECRET_KEY)

def fetch_ohlcv(symbol, interval="1d", limit=100):
    """
    Lấy dữ liệu OHLCV từ Binance API.
    """
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        logging.info(f"Lấy thành công dữ liệu OHLCV cho {symbol}.")
        return df
    except Exception as e:
        logging.error(f"Lỗi khi lấy dữ liệu OHLCV cho {symbol}: {e}")
        return pd.DataFrame()

def search_tokens(filter_func):
    """
    Search for tokens on Binance that satisfy a given condition.
    
    :param filter_func: A function that takes a token dictionary and returns True or False.
    :return: List of tokens that satisfy the filter condition.
    """
    try:
        # Fetch all symbols from Binance
        exchange_info = client.get_exchange_info()
        symbols = exchange_info.get("symbols", [])
        tokens = [
            {"symbol": symbol["symbol"], "status": symbol["status"]}
            for symbol in symbols if symbol["status"] == "TRADING"
        ]

        # Apply the filter function
        filtered_tokens = [token for token in tokens if filter_func(token)]
        logging.info(f"Found {len(filtered_tokens)} tokens matching the criteria.")
        return filtered_tokens
    except Exception as e:
        logging.error(f"Error fetching tokens: {e}")
        return []