import ccxt, argparse, time, os, json
from core.database import connect, insert_candles

ap = argparse.ArgumentParser()
ap.add_argument("--symbol", type=str, required=True)       # e.g. BTC/USDT:USDT or BTC/USDT
ap.add_argument("--days", type=int, default=1460)
ap.add_argument("--since", type=int, default=None, help="Unix ms since timestamp to start fetching")
ap.add_argument("--timeframe", type=str, default="5m")
ap.add_argument("--db", type=str, required=True)
ap.add_argument("--exchange", type=str, default="bitget")
ap.add_argument("--progress-file", type=str, default=None)
args = ap.parse_args()

# Helper: convert timeframe string to minutes
def tf_to_minutes(tf: str) -> int:
    if tf.endswith('m'):
        return int(tf[:-1])
    if tf.endswith('h'):
        return int(tf[:-1]) *60
    if tf.endswith('d'):
        return int(tf[:-1]) *60 *24
    raise ValueError(f"Unsupported timeframe: {tf}")

# Normalize symbol for target exchange
def normalize_symbol_for_exchange(sym: str, exchange: str) -> str:
    # If symbol uses Bitget contract format 'BTC/USDT:USDT', map to 'BTC/USDT'
    if ':' in sym:
        base = sym.split(':')[0]
        return base
    return sym

exchange_id = args.exchange.lower()

# Build exchange instance with reasonable defaults
exchange_options = {}
if 'bitget' in exchange_id:
    exchange_options = {"options": {"defaultType": "swap"}}
elif 'binance' in exchange_id:
    # use futures (USDT-margined) by default
    exchange_options = {"options": {"defaultType": "future"}}

try:
    ExchangeClass = getattr(ccxt, exchange_id)
except Exception:
    raise SystemExit(f"Exchange not supported by ccxt: {args.exchange}")

ex = ExchangeClass(exchange_options)
ms = ex.load_markets()

symbol = normalize_symbol_for_exchange(args.symbol, exchange_id)
if symbol not in ms:
    # try alternative format (some exchanges use different symbols)
    # attempt uppercase and simple replacements
    alt = symbol.replace(':', '_')
    if alt not in ms:
        raise SystemExit(f"Symbol {symbol} not found in {exchange_id} markets.")

# Target range
now_ms = int(time.time() *1000)
if args.since:
    since_ms = int(args.since)
else:
    since_ms = int((time.time() - args.days *24 *60 *60) *1000)
limit =1000 # desired; exchange may return less (Bitget often returns200)

# DB connection
conn = connect(args.db, timeframe=args.timeframe)

count =0
start = time.time()

# estimate total candles for progress (approx)
minutes = tf_to_minutes(args.timeframe)
estimated_total = int(((now_ms - since_ms) /1000) /60 / minutes)

last_fetched_ms = None

# fetch loop with retries
while since_ms < now_ms:
    try:
        # defensive: avoid identical since value loop
        if last_fetched_ms is not None and since_ms <= last_fetched_ms:
            since_ms = last_fetched_ms +1

        attempt =0
        max_attempts =5
        ohlcv = None
        while attempt < max_attempts:
            try:
                ohlcv = ex.fetch_ohlcv(symbol, args.timeframe, since=since_ms, limit=limit)
                break
            except ccxt.NetworkError:
                attempt +=1
                time.sleep(min(2 ** attempt,10))
            except Exception:
                attempt +=1
                time.sleep(1)
        if ohlcv is None:
            # give up this window
            break

        if not ohlcv:
            break

        rows = []
        for t, o, h, l, c, v in ohlcv:
            # convert ms -> seconds for DB (legacy code expects seconds)
            rows.append((int(t //1000), float(o), float(h), float(l), float(c), float(v)))

        insert_candles(conn, rows)
        count += len(rows)

        last_fetched_ms = ohlcv[-1][0]
        # advance since to last timestamp +1ms
        since_ms = ohlcv[-1][0] +1

        # progress
        if args.progress_file:
            elapsed = time.time() - start
            percent = min(100.0, (count / max(1, estimated_total)) *100.0)
            prog = {"total": estimated_total, "done": count, "elapsed_sec": elapsed, "eta_sec": None, "percent": percent}
            os.makedirs(os.path.dirname(args.progress_file), exist_ok=True)
            open(args.progress_file, "w").write(json.dumps(prog))

        # polite sleep to avoid rate limits
        time.sleep(0.2)

        # If exchange returns fewer than requested and we are far from now, continue anyway
        # but guard against infinite loops: if the last fetched timestamp does not advance, break
        if ohlcv and len(ohlcv) <1:
            break

    except Exception as e:
        # log and retry a bit, but don't infinite loop
        try:
            errfn = os.path.join('data', 'backfill_errors.log')
            os.makedirs(os.path.dirname(errfn), exist_ok=True)
            open(errfn, 'a', encoding='utf-8').write(f"{time.time()}: error fetching ohlcv: {e}\n")
        except Exception:
            pass
        time.sleep(2)
        continue

print(json.dumps({"inserted": count, "db": args.db}))