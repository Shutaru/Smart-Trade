import sqlite3
import os
import time
import json


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


def connect_lab(path="data/lab.db"):
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