import ccxt, argparse, time, os, json
from db_sqlite import connect, insert_candles

ap = argparse.ArgumentParser()
ap.add_argument("--symbol", type=str, required=True)       # e.g. BTC/USDT:USDT
ap.add_argument("--days", type=int, default=1460)
ap.add_argument("--timeframe", type=str, default="5m")
ap.add_argument("--db", type=str, required=True)
ap.add_argument("--progress-file", type=str, default=None)
args = ap.parse_args()

ex = ccxt.bitget({"options": {"defaultType": "swap"}})
ms = ex.load_markets()
if args.symbol not in ms:
    raise SystemExit(f"Symbol {args.symbol} not in Bitget markets.")

since = int((time.time() - args.days*24*60*60)*1000)
limit = 1000
conn = connect(args.db)

count = 0; total = None; start = time.time()
while True:
    ohlcv = ex.fetch_ohlcv(args.symbol, args.timeframe, since=since, limit=limit)
    if not ohlcv: break
    rows = []
    for t,o,h,l,c,v in ohlcv:
        rows.append((int(t//1000), float(o), float(h), float(l), float(c), float(v)))
    insert_candles(conn, rows)
    count += len(rows)
    since = ohlcv[-1][0] + 1
    if args.progress_file:
        elapsed = time.time()-start
        prog = {"total": -1, "done": count, "elapsed_sec": elapsed, "eta_sec": None}
        os.makedirs(os.path.dirname(args.progress_file), exist_ok=True)
        open(args.progress_file,"w").write(json.dumps(prog))
    if len(ohlcv) < limit:
        break

print(json.dumps({"inserted": count, "db": args.db}))