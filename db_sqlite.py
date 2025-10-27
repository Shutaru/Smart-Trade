import sqlite3, os, time

def connect(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS candles_5m (
        ts INTEGER PRIMARY KEY,
        open REAL, high REAL, low REAL, close REAL, volume REAL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS features_5m (
        ts INTEGER PRIMARY KEY,
        ema20 REAL, ema50 REAL, atr14 REAL, rsi5 REAL, rsi14 REAL, adx14 REAL,
        bb_mid REAL, bb_lo REAL, bb_up REAL, dn55 REAL, up55 REAL,
        regime_1h TEXT, macro_4h TEXT, atr1h_pct REAL
    )""")
    conn.commit()
    return conn

def insert_candles(conn, rows):
    conn.executemany("INSERT OR REPLACE INTO candles_5m(ts,open,high,low,close,volume) VALUES (?,?,?,?,?,?)", rows)
    conn.commit()

def insert_features(conn, rows):
    conn.executemany("INSERT OR REPLACE INTO features_5m VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()

def load_range(conn, start_ts, end_ts):
    cur = conn.cursor()
    cur.execute("SELECT ts,open,high,low,close,volume FROM candles_5m WHERE ts>=? AND ts<? ORDER BY ts ASC", (start_ts, end_ts))
    return cur.fetchall()