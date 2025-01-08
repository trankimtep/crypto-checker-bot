import json
import os
import logging

# Đường dẫn lưu dữ liệu
DATA_FILE = "needed_tokens.json"

def save_needed_tokens(tokens):
    """
    Lưu danh sách các token vào file JSON.
    :param tokens: Danh sách các token.
    """
    try:
        with open(DATA_FILE, "w") as file:
            json.dump(tokens, file)
        logging.info(f"Đã lưu danh sách token vào {DATA_FILE}.")
    except Exception as e:
        logging.error(f"Lỗi khi lưu danh sách token: {e}")

def load_needed_tokens():
    """
    Tải danh sách các token từ file JSON.
    :return: Danh sách các token hoặc danh sách rỗng nếu lỗi.
    """
    if not os.path.exists(DATA_FILE):
        logging.warning(f"File {DATA_FILE} không tồn tại. Trả về danh sách rỗng.")
        return []

    try:
        with open(DATA_FILE, "r") as file:
            tokens = json.load(file)
        logging.info(f"Đã tải danh sách token từ {DATA_FILE}.")
        return tokens
    except Exception as e:
        logging.error(f"Lỗi khi tải danh sách token: {e}")
        return []
