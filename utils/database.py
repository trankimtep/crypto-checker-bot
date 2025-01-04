import sqlite3

def init_db():
    conn = sqlite3.connect('data/tokens.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY,
            name TEXT,
            symbol TEXT,
            bought_price REAL
        )
    ''')
    conn.commit()
    conn.close()

def add_token(name, symbol, bought_price):
    conn = sqlite3.connect('data/tokens.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tokens (name, symbol, bought_price) VALUES (?, ?, ?)', 
                   (name, symbol, bought_price))
    conn.commit()
    conn.close()

def delete_token(symbol):
    conn = sqlite3.connect('data/tokens.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tokens WHERE symbol = ?', (symbol,))
    conn.commit()
    conn.close()

def list_tokens():
    conn = sqlite3.connect('data/tokens.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tokens')
    tokens = cursor.fetchall()
    conn.close()
    return tokens
