import logging
import pandas as pd
from ta.trend import MACD, IchimokuIndicator, ADXIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_SECRET_KEY

# Khởi tạo Binance client
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_SECRET_KEY)

def fetch_ohlcv(symbol, interval="1d", limit=100):
    """
    Lấy dữ liệu OHLCV (Open, High, Low, Close, Volume) từ Binance API.
    :param symbol: Tên cặp giao dịch, ví dụ: BTCUSDT
    :param interval: Khung thời gian, ví dụ: 1h, 1d
    :param limit: Số lượng nến cần lấy
    :return: DataFrame chứa dữ liệu OHLCV
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

def check_ma(df):
    """
    Kiểm tra tiêu chí MA10 > MA20 > MA50.
    :param df: DataFrame chứa dữ liệu OHLCV
    :return: True nếu thỏa mãn, False nếu không
    """
    try:
        ma10 = SMAIndicator(close=df["close"], window=10).sma_indicator()
        ma20 = SMAIndicator(close=df["close"], window=20).sma_indicator()
        ma50 = SMAIndicator(close=df["close"], window=50).sma_indicator()

        if ma10.iloc[-1] > ma20.iloc[-1] > ma50.iloc[-1]:
            logging.info(f"MA10 > MA20 > MA50: MA10={ma10.iloc[-1]}, MA20={ma20.iloc[-1]}, MA50={ma50.iloc[-1]}.")
            return True
        logging.info(f"Không thỏa mãn MA10 > MA20 > MA50: MA10={ma10.iloc[-1]}, MA20={ma20.iloc[-1]}, MA50={ma50.iloc[-1]}.")
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra MA: {e}")
        return False

def check_ichimoku(df):
    """
    Kiểm tra tiêu chí Ichimoku.
    Giá nằm trên mây Kumo, Tenkan cắt lên Kijun.
    :param df: DataFrame chứa dữ liệu OHLCV
    :return: True nếu thỏa mãn, False nếu không
    """
    try:
        ichimoku = IchimokuIndicator(
            high=df["high"], low=df["low"], window1=9, window2=26, window3=52
        )
        tenkan = ichimoku.ichimoku_conversion_line()
        kijun = ichimoku.ichimoku_base_line()
        senkou_span_a = ichimoku.ichimoku_a()
        senkou_span_b = ichimoku.ichimoku_b()

        if (tenkan.iloc[-1] > kijun.iloc[-1] and
                df["close"].iloc[-1] > max(senkou_span_a.iloc[-1], senkou_span_b.iloc[-1])):
            return True
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra Ichimoku: {e}")
        return False

def check_macd(df):
    """
    Kiểm tra tiêu chí MACD: MACD cắt lên Signal và histogram dương, tăng dần.
    :param df: DataFrame chứa dữ liệu OHLCV
    :return: True nếu thỏa mãn, False nếu không
    """
    try:
        macd = MACD(close=df["close"])
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        histogram = macd.macd_diff()

        if (macd_line.iloc[-1] > signal_line.iloc[-1] and
                histogram.iloc[-1] > 0 and
                histogram.iloc[-1] > histogram.iloc[-2]):
            return True
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra MACD: {e}")
        return False

def check_rsi(df):
    """
    Kiểm tra tiêu chí RSI: RSI trên 50 và đang tăng, hoặc vượt 70 với khối lượng lớn.
    :param df: DataFrame chứa dữ liệu OHLCV
    :return: True nếu thỏa mãn, False nếu không
    """
    try:
        rsi = RSIIndicator(close=df["close"]).rsi()
        if rsi.iloc[-1] > 50 and (rsi.iloc[-1] < 70 or df["volume"].iloc[-1] > df["volume"].mean()):
            return True
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra RSI: {e}")
        return False

def check_dmi(df):
    """
    Kiểm tra tiêu chí DMI: DI+ cắt lên DI-, ADX > 20.
    :param df: DataFrame chứa dữ liệu OHLCV
    :return: True nếu thỏa mãn, False nếu không
    """
    try:
        dmi = ADXIndicator(high=df["high"], low=df["low"], close=df["close"])
        adx = dmi.adx()
        di_plus = dmi.adx_pos()
        di_minus = dmi.adx_neg()

        if di_plus.iloc[-1] > di_minus.iloc[-1] and adx.iloc[-1] > 20:
            return True
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra DMI: {e}")
        return False

def token_meets_criteria(token):
    """
    Kiểm tra tất cả tiêu chí mua.
    :param token: dict chứa thông tin token (symbol)
    :return: True nếu thỏa mãn tất cả tiêu chí, False nếu không
    """
    logging.info("Hàm token_meets_criteria được gọi.")
    symbol = token["symbol"]

    if not symbol.endswith("USDT"):
        return False

    # Lấy dữ liệu OHLCV
    df = fetch_ohlcv(symbol, interval="1d", limit=100)
    if df.empty:
        logging.warning(f"Không có dữ liệu cho {symbol}.")
        return False

    # Kiểm tra từng tiêu chí
    #if (check_ma(df) and check_ichimoku(df) and check_macd(df) and check_rsi(df) and check_dmi(df)):
    if (check_ma(df) and check_ichimoku(df) and check_macd(df) and check_rsi(df) and check_dmi(df)):
        logging.info(f"Token {symbol} thỏa mãn tất cả tiêu chí mua.")
        return True

    logging.info(f"Token {symbol} không thỏa mãn tiêu chí mua.")
    return False
