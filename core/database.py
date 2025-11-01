import sqlite3
import os
import time
import json


def get_db_path(exchange: str, symbol: str, timeframe: str) -> str:
    """Generate database path for a specific symbol and timeframe"""
    symbol_safe = symbol.replace("/", "_").replace(":", "_")
    db_dir = os.path.join("data", "lab", exchange)
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, f"{symbol_safe}_{timeframe}.db")


def get_candles_table(timeframe: str) -> str:
    """Get candles table name for timeframe"""
    return f"candles_{timeframe.replace('m', 'min').replace('h', 'hr').replace('d', 'day')}"


def get_features_table(timeframe: str) -> str:
    """Get features table name for timeframe"""
    return f"features_{timeframe.replace('m', 'min').replace('h', 'hr').replace('d', 'day')}"


def connect(path: str, timeframe: str = "5m"):
    """Connect to database and ensure tables exist"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    
    candles_table = get_candles_table(timeframe)
    features_table = get_features_table(timeframe)
    
    # Create candles table
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {candles_table} (
        ts INTEGER PRIMARY KEY,
        open REAL, high REAL, low REAL, close REAL, volume REAL
    )""")
    
    # Create features table with dynamic columns
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {features_table} (
        ts INTEGER PRIMARY KEY,
        close REAL,
        volume REAL,
        rsi_14 REAL,
        rsi_7 REAL,
        ema_20 REAL,
        ema_50 REAL,
        ema_200 REAL,
        sma_20 REAL,
        sma_50 REAL,
        sma_200 REAL,
        atr_14 REAL,
        adx_14 REAL,
        bb_upper REAL,
        bb_middle REAL,
        bb_lower REAL,
        macd REAL,
        macd_signal REAL,
        macd_hist REAL
    )""")
    
    conn.commit()
    return conn


def connect_lab(path="data/lab.db"):
    """Connect to lab metadata database"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    
    cur.execute("""CREATE TABLE IF NOT EXISTS runs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        mode TEXT NOT NULL,
        exchange TEXT,
        symbols TEXT,
        timeframe TEXT,
        objective TEXT,
        status TEXT DEFAULT 'pending',
        config_json TEXT,
        created_at INTEGER,
        updated_at INTEGER,
        started_at INTEGER,
        completed_at INTEGER
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS trials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        trial_number INTEGER,
        params_json TEXT,
        metrics_json TEXT,
        score REAL,
        created_at INTEGER,
        FOREIGN KEY (run_id) REFERENCES runs(id)
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS artifacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        trial_id INTEGER,
        name TEXT NOT NULL,
        path TEXT NOT NULL,
        created_at INTEGER,
        FOREIGN KEY (run_id) REFERENCES runs(id),
        FOREIGN KEY (trial_id) REFERENCES trials(id)
    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        ts INTEGER,
        level TEXT,
        message TEXT,
        FOREIGN KEY (run_id) REFERENCES runs(id)
    )""")
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trials_run ON trials(run_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_run ON artifacts(run_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_run ON logs(run_id)")
    
    conn.commit()
    return conn


def insert_candles_bulk(conn, timeframe: str, rows):
    """Insert candles in bulk"""
    table = get_candles_table(timeframe)
    conn.executemany(
        f"INSERT OR REPLACE INTO {table} (ts,open,high,low,close,volume) VALUES (?,?,?,?,?,?)",
        rows
    )
    conn.commit()


def insert_features_bulk(conn, timeframe: str, rows):
    """Insert features in bulk (ts, close, volume, indicators...)"""
    table = get_features_table(timeframe)
    placeholders = ','.join(['?'] * len(rows[0]))
    conn.executemany(
        f"INSERT OR REPLACE INTO {table} VALUES ({placeholders})",
        rows
    )
    conn.commit()


def load_candles(conn, timeframe: str, start_ts: int = None, end_ts: int = None):
    """Load candles from database"""
    table = get_candles_table(timeframe)
    cur = conn.cursor()
    
    if start_ts and end_ts:
        cur.execute(
            f"SELECT ts,open,high,low,close,volume FROM {table} WHERE ts>=? AND ts<? ORDER BY ts ASC",
            (start_ts, end_ts)
        )
    else:
        cur.execute(f"SELECT ts,open,high,low,close,volume FROM {table} ORDER BY ts ASC")
    
    return cur.fetchall()


def count_candles(conn, timeframe: str) -> int:
    """Count candles in database"""
    table = get_candles_table(timeframe)
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0]


# Legacy functions for backward compatibility
def insert_candles(conn, rows):
    """Legacy: Insert candles for 5m timeframe"""
    insert_candles_bulk(conn, "5m", rows)


def insert_features(conn, rows):
    """Legacy: Insert features for 5m timeframe"""
    insert_features_bulk(conn, "5m", rows)


def load_range(conn, start_ts, end_ts):
    """Legacy: Load 5m candles"""
    return load_candles(conn, "5m", start_ts, end_ts)


# Run management functions
def create_run(conn, run_id, name, mode, config):
    now = int(time.time())
    data = config.get('data', {})
    obj = config.get('objective', {})
    
    cur = conn.cursor()
    cur.execute("""INSERT INTO runs 
        (id, name, mode, exchange, symbols, timeframe, objective, status, config_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, name, mode, data.get('exchange'), json.dumps(data.get('symbols', [])), 
         data.get('timeframe'), obj.get('expression'), 'pending', json.dumps(config), now, now))
    conn.commit()
    return run_id


def update_run_status(conn, run_id, status, **kwargs):
    now = int(time.time())
    fields = ["status = ?", "updated_at = ?"]
    values = [status, now]
    
    if 'started_at' in kwargs:
        fields.append("started_at = ?")
        values.append(kwargs['started_at'])
    if 'completed_at' in kwargs:
        fields.append("completed_at = ?")
        values.append(kwargs['completed_at'])
    
    values.append(run_id)
    
    cur = conn.cursor()
    cur.execute(f"UPDATE runs SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()


def insert_trial(conn, run_id, trial_number, params, metrics, score):
    cur = conn.cursor()
    cur.execute("""INSERT INTO trials 
        (run_id, trial_number, params_json, metrics_json, score, created_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (run_id, trial_number, json.dumps(params), json.dumps(metrics), score, int(time.time())))
    conn.commit()
    return cur.lastrowid


def insert_artifact(conn, run_id, trial_id, name, path):
    cur = conn.cursor()
    cur.execute("""INSERT INTO artifacts (run_id, trial_id, name, path, created_at)
        VALUES (?, ?, ?, ?, ?)""",
        (run_id, trial_id, name, path, int(time.time())))
    conn.commit()
    return cur.lastrowid


def insert_log(conn, run_id, level, message):
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (run_id, ts, level, message) VALUES (?, ?, ?, ?)",
                (run_id, int(time.time()), level, message))
    conn.commit()


def get_run(conn, run_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    row = cur.fetchone()
    if not row:
        return None
    
    columns = [desc[0] for desc in cur.description]
    return dict(zip(columns, row))


def get_run_trials(conn, run_id, limit=100, offset=0):
    cur = conn.cursor()
    cur.execute("""SELECT * FROM trials 
        WHERE run_id = ? 
        ORDER BY score DESC 
        LIMIT ? OFFSET ?""", (run_id, limit, offset))
    
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in rows]


def get_all_runs(conn, limit=100):
    cur = conn.cursor()
    cur.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,))
    
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in rows]