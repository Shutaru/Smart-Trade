"""
Binance ETH/USDT Fetcher - Download historical data for Ethereum

Usage:
    python fetch_eth.py --days 90 --timeframe 5m
    python fetch_eth.py --since 1704067200000 --timeframe 1h
"""

import ccxt
import argparse
import time
import os
import yaml
from db_sqlite import connect, insert_candles_bulk

# Parse arguments
ap = argparse.ArgumentParser(description="Fetch ETH/USDT data from Binance")
ap.add_argument("--days", type=int, default=90, help="Days of history to fetch")
ap.add_argument("--since", type=int, default=None, help="Unix ms timestamp to start from")
ap.add_argument("--timeframe", type=str, default="5m", help="Candle timeframe (1m, 5m, 15m, 1h, 4h)")
ap.add_argument("--db", type=str, default=None, help="Database path (auto-generated if not specified)")
args = ap.parse_args()

# Binance setup (USDT-M Futures for better data)
symbol = "ETH/USDT"
exchange = ccxt.binance({
    "enableRateLimit": True,
    "rateLimit": 50,
    "options": {"defaultType": "future"}
})

print(f"[ETH Fetcher] Connecting to Binance Futures...")
markets = exchange.load_markets()

if symbol not in markets:
    print(f"❌ Symbol {symbol} not found on Binance Futures!")
    exit(1)

print(f"✅ Found {symbol} on Binance Futures")

# Database path
if args.db:
    db_path = args.db
else:
    db_path = os.path.join("data", "db", f"ETH_USDT_{args.timeframe}.db")

os.makedirs(os.path.dirname(db_path), exist_ok=True)
print(f"\n📁 Database: {db_path}")

conn = connect(db_path, timeframe=args.timeframe)

# Calculate time range
now_ms = int(time.time() * 1000)
if args.since:
    since_ms = args.since
else:
    since_ms = now_ms - (args.days * 24 * 60 * 60 * 1000)

start_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(since_ms / 1000))
end_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(now_ms / 1000))

print(f"\n⏱️  Fetching data:")
print(f"   From: {start_date}")
print(f"   To:   {end_date}")
print(f"   Timeframe: {args.timeframe}")

# Fetch data
limit = 1000
count = 0
requests_made = 0
max_requests = 100
last_ts = None

print(f"\n🔄 Starting download...\n")

while since_ms < now_ms and requests_made < max_requests:
    try:
        if last_ts is not None and since_ms <= last_ts:
            since_ms = last_ts + 1
        
        attempt = 0
        max_attempts = 5
        ohlcv = None
        
        while attempt < max_attempts:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, args.timeframe, since=since_ms, limit=limit)
                break
            except ccxt.NetworkError:
                attempt += 1
                wait = min(2 ** attempt, 10)
                print(f"   Network error, retrying in {wait}s...")
                time.sleep(wait)
            except ccxt.RateLimitExceeded:
                attempt += 1
                wait = min(2 ** attempt, 20)
                print(f"   Rate limit, waiting {wait}s...")
                time.sleep(wait)
            except Exception as e:
                print(f"   Error: {e}")
                attempt += 1
                time.sleep(1)
        
        if ohlcv is None:
            print(f"   Failed to fetch data")
            break
        
        if not ohlcv:
            print(f"   No more data")
            break
        
        # Convert to database format
        rows = []
        for t, o, h, l, c, v in ohlcv:
            rows.append((int(t // 1000), float(o), float(h), float(l), float(c), float(v)))
        
        insert_candles_bulk(conn, args.timeframe, rows)
        count += len(rows)
        requests_made += 1
        
        last_ts = ohlcv[-1][0]
        since_ms = last_ts + 1
        
        progress_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(last_ts / 1000))
        progress_pct = min(100, ((last_ts - (now_ms - args.days * 24 * 60 * 60 * 1000)) / (args.days * 24 * 60 * 60 * 1000)) * 100)
        
        print(f"   [{requests_made:3d}] {len(ohlcv):4d} candles | {progress_date} ({progress_pct:.1f}%)")
        
        if len(ohlcv) < limit:
            break
        
        time.sleep(0.2)
    
    except Exception as e:
        print(f"   Error: {e}")
        time.sleep(2)
        continue

conn.close()

print(f"\n✅ Download complete!")
print(f"   Total: {count:,} candles")
print(f"   Database: {db_path}")

# Update config
try:
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    
    cfg['symbol'] = symbol
    cfg['db'] = {'path': db_path}
    
    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    
    print(f"\n📝 Updated config.yaml")
except Exception as e:
    print(f"\n⚠️  Could not update config: {e}")

print(f"\n🚀 Ready to backtest ETH!")