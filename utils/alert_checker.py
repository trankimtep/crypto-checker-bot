from utils.database import list_tokens
from utils.binance_api import client

def check_conditions():
    tokens = list_tokens()
    alerts = []
    for token in tokens:
        price = float(client.get_symbol_ticker(symbol=token[2])['price'])
        if price > token[3] * 1.2:  # Ví dụ: giá tăng 20%
            alerts.append(f"Token {token[1]} ({token[2]}) đã tăng lên {price}")
    return alerts

