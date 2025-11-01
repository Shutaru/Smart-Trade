"""Check database contents and available data"""

import yaml
import time
from core.database import connect

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

conn = connect(cfg['db']['path'])
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]

print("="*80)
print("DATABASE INSPECTION")
print("="*80)
print(f"\nDatabase: {cfg['db']['path']}")
print(f"\nTables: {tables}")

if 'candles_5m' in tables:
    print("\n" + "="*80)
    print("CANDLES_5M TABLE")
    print("="*80)
    
    cursor.execute("SELECT COUNT(*) FROM candles_5m")
    total = cursor.fetchone()[0]
    print(f"Total candles: {total:,}")
    
    cursor.execute("SELECT MIN(ts_open), MAX(ts_open) FROM candles_5m")
    min_ts, max_ts = cursor.fetchone()
    
    if min_ts and max_ts:
        min_date = time.strftime("%Y-%m-%d %H:%M", time.localtime(min_ts))
        max_date = time.strftime("%Y-%m-%d %H:%M", time.localtime(max_ts))
        
        print(f"Date range: {min_date} to {max_date}")
        
        days = (max_ts - min_ts) / (24 * 60 * 60)
        print(f"Duration: {days:.1f} days")
        
        print("\nSample (first 5 candles):")
        cursor.execute("SELECT ts_open, open, high, low, close, volume FROM candles_5m ORDER BY ts_open LIMIT 5")
        rows = cursor.fetchall()
        
        print(f"{'Timestamp':<20} {'Open':>12} {'High':>12} {'Low':>12} {'Close':>12}")
        print("-" * 80)
        
        for row in rows:
            ts_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(row[0]))
            print(f"{ts_str:<20} {row[1]:>12.4f} {row[2]:>12.4f} {row[3]:>12.4f} {row[4]:>12.4f}")

print("\n" + "="*80)

# Check for symbol column
cursor.execute("PRAGMA table_info(candles_5m)")
columns = [col[1] for col in cursor.fetchall()]
print(f"\nColumns in candles_5m: {columns}")

if 'symbol' in columns:
    cursor.execute("SELECT DISTINCT symbol FROM candles_5m")
    symbols = [s[0] for s in cursor.fetchall()]
    print(f"\nSymbols in database: {symbols}")
else:
    print("\nNo 'symbol' column - single asset database (probably BTC)")

conn.close()