from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_SECRET_KEY

client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_SECRET_KEY)

def search_tokens(criteria):

    tokens = client.get_all_tickers()
    matched_tokens = []
    for token in tokens:
        if criteria(token):  # `criteria` là một hàm kiểm tra điều kiện
            matched_tokens.append(token)
    return matched_tokens
