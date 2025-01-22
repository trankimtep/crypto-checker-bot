# utils/database.py

import pickle
import os

CACHE_FILE = "cache.pkl"

def save_needed_tokens(tokens):
    """
    Lưu token vào cache.
    """
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(tokens, f)

def load_needed_tokens():
    """
    Tải token từ cache.
    """
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return []
