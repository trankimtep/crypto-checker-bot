import logging
import pandas as pd
from ta.trend import MACD, IchimokuIndicator, ADXIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_SECRET_KEY

# Khởi tạo Binance client
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_SECRET_KEY)

def fetch_ohlcv(symbol, interval="1d", limit=100):

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

    try:
        rsi = RSIIndicator(close=df["close"]).rsi()
        if rsi.iloc[-1] > 30 and (rsi.iloc[-1] < 70 or df["volume"].iloc[-1] > df["volume"].mean()):
            return True
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra RSI: {e}")
        return False

def check_dmi(df):

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

def check_volume(df):

    try:
        # Tính trung bình khối lượng 50 phiên gần nhất
        average_volume_50 = df["volume"].rolling(window=50).mean()

        # Kiểm tra khối lượng phiên cuối cùng
        if df["volume"].iloc[-1] >= 1.2 * average_volume_50.iloc[-1]:
            logging.info(f"Khối lượng giao dịch thỏa mãn: {df['volume'].iloc[-1]} >= 1.2 * {average_volume_50.iloc[-1]}.")
            return True
        logging.info(f"Khối lượng giao dịch không thỏa mãn: {df['volume'].iloc[-1]} < 1.2 * {average_volume_50.iloc[-1]}.")
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra khối lượng giao dịch: {e}")
        return False

def check_price_cross_ma10_realtime(df, symbol):

    try:
        # Lấy giá hiện tại từ Binance
        current_price = float(client.get_symbol_ticker(symbol=symbol)["price"])
        
        # Tính MA10 dựa trên dữ liệu lịch sử
        ma10 = SMAIndicator(close=df["close"], window=10).sma_indicator()
        
        # Giá đóng cửa trước đó
        previous_close = df["close"].iloc[-1]
        
        # Kiểm tra điều kiện cắt lên
        if previous_close < ma10.iloc[-1] and current_price > ma10.iloc[-1]:
            logging.info(f"Giá hiện tại cắt lên MA10: Previous Close={previous_close}, Current Price={current_price}, MA10={ma10.iloc[-1]}.")
            return True
        logging.info(f"Giá hiện tại không cắt lên MA10: Previous Close={previous_close}, Current Price={current_price}, MA10={ma10.iloc[-1]}.")
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra giá hiện tại cắt lên MA10: {e}")
        return False

def check_conditions_needed(df):

    try:
        # Danh sách các điều kiện
        conditions = [
            check_ma(df),
            check_ichimoku(df),
            check_macd(df),
            check_rsi(df),
            check_dmi(df)
        ]
        
        # Đếm số lượng điều kiện thỏa mãn
        satisfied_conditions = sum(conditions)
        
        if satisfied_conditions >= 4:
            logging.info(f"Thỏa mãn {satisfied_conditions}/5 điều kiện cần.")
            return True
        else:
            logging.info(f"Chỉ thỏa mãn {satisfied_conditions}/5 điều kiện cần.")
            return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra điều kiện cần: {e}")
        return False


def check_conditions_sufficient(df, symbol):

    return (check_volume(df) and check_price_cross_ma10_realtime(df, symbol))



