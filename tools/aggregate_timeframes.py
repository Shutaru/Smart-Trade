"""
Aggregate higher timeframes (e.g.1h,4h) from5m candles stored in SQLite.

Usage:
 python tools/aggregate_timeframes.py --db data/db/BTC_USDT_USDT_5m.db --from-tf5m --to-tf1h --since-ms <unix_ms>

This will create/replace table `candles_{to_tbl}` where `to_tbl` is e.g. `candles_1hr`.

The script expects candles stored with columns: ts (seconds), open, high, low, close, volume.
Outputs ts as seconds (start of candle).
"""
import argparse
import sqlite3
import time
from datetime import datetime, timezone

ap = argparse.ArgumentParser()
ap.add_argument('--db', required=True)
ap.add_argument('--from-tf', default='5m')
ap.add_argument('--to-tf', required=True)
ap.add_argument('--since-ms', type=int, default=None)
args = ap.parse_args()

TF_MINUTES = {
 '1m':1, '3m':3, '5m':5, '15m':15, '30m':30,
 '1h':60, '4h':240, '1d':1440
}

if args.from_tf not in TF_MINUTES or args.to_tf not in TF_MINUTES:
 raise SystemExit('Unsupported timeframe')

from_min = TF_MINUTES[args.from_tf]
to_min = TF_MINUTES[args.to_tf]
if to_min % from_min !=0:
 raise SystemExit('to-tf must be a multiple of from-tf')

ratio = to_min // from_min

conn = sqlite3.connect(args.db)
cur = conn.cursor()

# determine input table
in_tbl_candidate = f"candles_{args.from_tf.replace('m','min').replace('h','hr').replace('d','day')}"
try:
 cur.execute(f"SELECT COUNT(*) FROM {in_tbl_candidate}")
 in_tbl = in_tbl_candidate
except Exception:
 in_tbl = 'candles'

# load rows
q = f"SELECT ts, open, high, low, close, volume FROM {in_tbl} ORDER BY ts ASC"
rows = []
for r in cur.execute(q):
 rows.append(r)

if not rows:
 print('No source rows found; aborting')
 conn.close()
 raise SystemExit(1)

# convert to lists and filter by since if provided
if args.since_ms:
 since_s = args.since_ms //1000
 rows = [r for r in rows if r[0] >= since_s]

# aggregate
out_rows = []
for i in range(0, len(rows), ratio):
 block = rows[i:i+ratio]
 if len(block) < ratio:
  break
 ts0 = block[0][0]
 o = block[0][1]
 h = max(b[2] for b in block)
 l = min(b[3] for b in block)
 c = block[-1][4]
 v = sum(b[5] for b in block)
 out_rows.append((int(ts0), float(o), float(h), float(l), float(c), float(v)))

# write to target table
out_tbl = f"candles_{args.to_tf.replace('m','min').replace('h','hr').replace('d','day')}"
cur.execute(f"CREATE TABLE IF NOT EXISTS {out_tbl} (ts INTEGER PRIMARY KEY, open REAL, high REAL, low REAL, close REAL, volume REAL)")
# insert/replace
cur.executemany(f"INSERT OR REPLACE INTO {out_tbl} (ts,open,high,low,close,volume) VALUES (?,?,?,?,?,?)", out_rows)
conn.commit()
print({"inserted": len(out_rows), "table": out_tbl, "db": args.db})
conn.close()
