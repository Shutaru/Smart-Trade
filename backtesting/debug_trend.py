"""
Debug script to test why trend strategies are not generating trades
"""

import yaml
import time
from core.database import connect, load_range
from core.features import compute_feature_rows
from strategies.registry import get_strategy, get_strategy_info
from strategies.adapter import build_indicator_dict, build_bar_dict, build_state_dict

# Load config
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

# Load data
conn = connect(cfg.get("db", {}).get("path", "data/bot.db"))
now = int(time.time())
start = now - 90 * 24 * 60 * 60

rows = load_range(conn, start, now)
ts = [r[0] for r in rows]
o = [r[1] for r in rows]
h = [r[2] for r in rows]
l = [r[3] for r in rows]
c = [r[4] for r in rows]
v = [r[5] for r in rows] if len(rows[0]) > 5 else None

print(f"Loaded {len(rows)} candles\n")

# Calculate features
feats_rows = compute_feature_rows(ts, o, h, l, c, v)

feat = {
    "ema20": [r[1] for r in feats_rows],
    "ema50": [r[2] for r in feats_rows],
    "ema200": [None] * len(feats_rows),
    "atr14": [r[3] for r in feats_rows],
    "rsi5": [r[4] for r in feats_rows],
    "rsi14": [r[5] for r in feats_rows],
    "adx14": [r[6] for r in feats_rows],
    "bb_mid": [r[7] for r in feats_rows],
    "bb_lo": [r[8] for r in feats_rows],
    "bb_up": [r[9] for r in feats_rows],
    "dn55": [r[10] for r in feats_rows],
    "up55": [r[11] for r in feats_rows],
    "regime": [r[12] for r in feats_rows],
    "macro": [r[13] for r in feats_rows],
    "atr1h_pct": [r[14] for r in feats_rows],
    "macd": [r[15] for r in feats_rows],
    "macd_signal": [r[16] for r in feats_rows],
    "macd_hist": [r[17] for r in feats_rows],
    "stoch_k": [r[18] for r in feats_rows],
    "stoch_d": [r[19] for r in feats_rows],
    "cci20": [r[20] for r in feats_rows],
    "williams_r": [r[21] for r in feats_rows],
    "supertrend": [r[22] for r in feats_rows],
    "supertrend_dir": [r[23] for r in feats_rows],
    "mfi14": [r[24] for r in feats_rows],
    "vwap": [r[25] for r in feats_rows],
    "obv": [r[26] for r in feats_rows],
    "keltner_mid": [r[27] for r in feats_rows],
    "keltner_lo": [r[28] for r in feats_rows],
    "keltner_up": [r[29] for r in feats_rows],
}

# Calculate EMA200
def ema(prices, period):
    result = [None] * len(prices)
    k = 2 / (period + 1)
    result[period - 1] = sum(prices[:period]) / period
    for i in range(period, len(prices)):
        result[i] = prices[i] * k + result[i-1] * (1 - k)
    return result

feat['ema200'] = ema(c, 200)

# Test strategy
strategy_name = "trendflow_supertrend"
strategy_fn = get_strategy(strategy_name)
info = get_strategy_info(strategy_name)

print(f"Testing: {strategy_name}")
print(f"Description: {info['description']}\n")

signals_found = 0
checked_bars = 0

for i in range(200, len(ts), 100):
    bar = build_bar_dict(i, o, h, l, c, v)
    ind = build_indicator_dict(i, ts, o, h, l, c, feat)
    state = build_state_dict(position=None, cooldown_bars_left=0)
    params = info.get('params', {})
    
    try:
        signal = strategy_fn(bar, ind, state, params)
        
        if signal:
            signals_found += 1
            print(f"[Bar {i}] SIGNAL: {signal['side']}")
            print(f"  Reason: {signal['reason']}")
            print(f"  Close: ${c[i]:,.2f}, EMA200: ${ind['ema200']:,.2f}")
            print(f"  ST: {'BULL' if ind['supertrend_bull'] else 'BEAR'}, ADX: {ind['adx14']:.1f}\n")
            
            if signals_found >= 5:
                break
        else:
            checked_bars += 1
            if checked_bars <= 3:
                print(f"[Bar {i}] No signal:")
                print(f"  Close: ${c[i]:,.2f}, EMA200: {ind.get('ema200', 'N/A')}")
                print(f"  Close>EMA200: {c[i] > ind.get('ema200', 0) if ind.get('ema200') else False}")
                print(f"  ST_bull: {ind.get('supertrend_bull')}, ADX: {ind.get('adx14', 0):.1f}\n")
    
    except Exception as e:
        print(f"[Bar {i}] ERROR: {e}\n")
        break

print(f"\nSUMMARY: {signals_found} signals found in {checked_bars + signals_found} bars checked")

if signals_found == 0:
    print("\nChecking indicator validity at bar 1000:")
    test_idx = min(1000, len(c) - 1)
    ind_test = build_indicator_dict(test_idx, ts, o, h, l, c, feat)
    
    for key in ['ema20', 'ema50', 'ema200', 'supertrend_bull', 'adx14', 'rsi14']:
        print(f"  {key}: {ind_test.get(key, 'MISSING')}")