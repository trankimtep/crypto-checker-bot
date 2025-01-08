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
        # Chỉ lưu giữ các cột cần thiết và chuyển đổi kiểu dữ liệu
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
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

def calculate_indicators(df):
    """
    Tính toán tất cả các chỉ báo cần thiết một lần.
    :param df: DataFrame chứa dữ liệu OHLCV
    :return: dict chứa các chỉ báo đã tính
    """
    try:
        if len(df) < 50:  # Kiểm tra nếu dữ liệu ít hơn 50 dòng
            logging.warning("Dữ liệu không đủ để tính toán các chỉ báo.")
            return {}

        indicators = {}
        indicators["ma10"] = SMAIndicator(close=df["close"], window=10).sma_indicator()
        indicators["ma20"] = SMAIndicator(close=df["close"], window=20).sma_indicator()
        indicators["ma50"] = SMAIndicator(close=df["close"], window=50).sma_indicator()

        ichimoku = IchimokuIndicator(
            high=df["high"], low=df["low"], window1=9, window2=26, window3=52
        )
        indicators["tenkan"] = ichimoku.ichimoku_conversion_line()
        indicators["kijun"] = ichimoku.ichimoku_base_line()
        indicators["senkou_a"] = ichimoku.ichimoku_a()
        indicators["senkou_b"] = ichimoku.ichimoku_b()

        macd = MACD(close=df["close"])
        indicators["macd_line"] = macd.macd()
        indicators["signal_line"] = macd.macd_signal()
        indicators["macd_histogram"] = macd.macd_diff()

        indicators["rsi"] = RSIIndicator(close=df["close"]).rsi()

        adx = ADXIndicator(high=df["high"], low=df["low"], close=df["close"])
        indicators["adx"] = adx.adx()
        indicators["di_plus"] = adx.adx_pos()
        indicators["di_minus"] = adx.adx_neg()

        indicators["volume_mean_50"] = df["volume"].rolling(window=50).mean()

        logging.info("Tính toán chỉ báo thành công.")
        return indicators
    except Exception as e:
        logging.error(f"Lỗi khi tính toán chỉ báo: {e}")
        return {}


def check_conditions_needed(df, indicators):
    """
    Kiểm tra nhóm điều kiện cần.
    :param df: DataFrame chứa dữ liệu OHLCV
    :param indicators: dict chứa các chỉ báo đã tính
    :return: True nếu thỏa mãn ít nhất 4/5 điều kiện cần, False nếu không
    """
    try:
        if not indicators:  # Kiểm tra nếu indicators rỗng
            logging.warning("Không thể kiểm tra điều kiện cần do thiếu chỉ báo.")
            return False

        conditions = [
            indicators["ma10"].iloc[-1] > indicators["ma20"].iloc[-1] > indicators["ma50"].iloc[-1],
            indicators["tenkan"].iloc[-1] > indicators["kijun"].iloc[-1] and
            df["close"].iloc[-1] > max(indicators["senkou_a"].iloc[-1], indicators["senkou_b"].iloc[-1]),
            indicators["macd_line"].iloc[-1] > indicators["signal_line"].iloc[-1] and
            indicators["macd_histogram"].iloc[-1] > 0 and
            indicators["macd_histogram"].iloc[-1] > indicators["macd_histogram"].iloc[-2],
            indicators["rsi"].iloc[-1] > 50,
            indicators["di_plus"].iloc[-1] > indicators["di_minus"].iloc[-1] and indicators["adx"].iloc[-1] > 20,
        ]
        satisfied_conditions = sum(conditions)
        logging.info(f"Điều kiện cần: {satisfied_conditions}/5 thỏa mãn.")
        return satisfied_conditions >= 4
    except KeyError as e:
        logging.error(f"Chỉ báo bị thiếu: {e}")
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra nhóm điều kiện cần: {e}")
        return False


def check_conditions_sufficient(df, indicators, symbol):
    """
    Kiểm tra nhóm điều kiện đủ.
    :param df: DataFrame chứa dữ liệu OHLCV
    :param indicators: dict chứa các chỉ báo đã tính
    :param symbol: Tên cặp giao dịch, ví dụ: BTCUSDT
    :return: True nếu thỏa mãn tất cả điều kiện đủ, False nếu không
    """
    try:
        current_price = float(client.get_symbol_ticker(symbol=symbol)["price"])
        is_volume_sufficient = df["volume"].iloc[-1] >= 1.2 * indicators["volume_mean_50"].iloc[-1]
        is_price_cross_ma10 = df["close"].iloc[-1] < indicators["ma10"].iloc[-1] and current_price > indicators["ma10"].iloc[-1]

        if is_volume_sufficient and is_price_cross_ma10:
            logging.info(f"Điều kiện đủ đạt: Volume và giá hiện tại cắt lên MA10.")
            return True
        logging.info(f"Điều kiện đủ không đạt: Volume hoặc giá không cắt lên MA10.")
        return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra nhóm điều kiện đủ: {e}")
        return False
