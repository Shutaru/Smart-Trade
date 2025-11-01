"""
Debug why strategies generate signals but don't execute trades

Tests the full pipeline: Signal ? Exit Plan ? Sizing ? Broker Execution
"""

import yaml
import time
from db_sqlite import connect, load_range
from features import compute_feature_rows
from strategy_registry import get_strategy, get_strategy_info
from indicator_adapter import build_indicator_dict, build_bar_dict, build_state_dict
from strategy_regime import build_regime_exit_plan
from sizing import compute_qty
from broker_futures_paper_v2 import PaperFuturesBrokerV2
from indicators import supertrend as calc_supertrend, keltner as calc_keltner
import os

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

# Add EMA200
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
print(f"Config account equity: {cfg.get('account', {}).get('starting_equity_usd', 100000)}")
print(f"Config sizing: {cfg.get('sizing', {})}")
print(f"Config risk: {cfg.get('risk', {})}")
print("\n" + "="*80 + "\n")

# Initialize broker
outdir = "data/debug_execution"
os.makedirs(outdir, exist_ok=True)

broker = PaperFuturesBrokerV2(
    equity=float(cfg.get("account", {}).get("starting_equity_usd", 100000)),
    max_daily_loss_pct=float(cfg.get("risk", {}).get("max_daily_loss_pct", 2.0)),
    spread_bps=float(cfg.get("fees", {}).get("spread_bps", 1.0)),
    taker_fee_bps=float(cfg.get("fees", {}).get("taker_fee_bps", 5.0)),
    maker_fee_bps=float(cfg.get("fees", {}).get("maker_fee_bps", 2.0)),
    data_dir=outdir
)

print(f"Broker initialized:")
print(f"  Equity: ${broker.equity:,.2f}")
print(f"  Position: {broker.position}")
print("\n" + "="*80 + "\n")

# Calculate trailing indicators
st_line, st_tr = calc_supertrend(h, l, c, n=10, mult=3.0)
kel_mid, kel_lo, kel_up = calc_keltner(h, l, c, n=20, mult=1.5)

# Find first signal
signals_tested = 0
first_signal_bar = None

for i in range(200, min(3000, len(ts)), 100):
    bar = build_bar_dict(i, o, h, l, c, v)
    ind = build_indicator_dict(i, ts, o, h, l, c, feat)
    state = build_state_dict(position=None, cooldown_bars_left=0)
    params = info.get('params', {})
    
    signal = strategy_fn(bar, ind, state, params)
    
    if signal and signal.get('side'):
     first_signal_bar = i
        signals_tested += 1
        
     print(f"[Bar {i}] SIGNAL DETECTED")
   print(f"  Side: {signal['side']}")
        print(f"  Reason: {signal['reason']}")
        print(f"  Close: ${c[i]:,.2f}")
        print(f"  ATR: ${feat['atr14'][i]:,.2f}")
        print()
        
        # Test full execution pipeline
        print("STEP 1: Build Exit Plan")
print("-" * 80)
        
        atr = feat['atr14'][i] or (c[i] * 0.01)
        side = signal['side']
    
     try:
            exit_plan = build_regime_exit_plan(
          side, c[i], atr, i, h, l, feat, cfg.get('risk', {})
       )
     
          print(f"  ? Exit Plan Created:")
         print(f"     Entry: ${exit_plan.entry:,.2f}")
         print(f"     SL: ${exit_plan.sl:,.2f}")
 print(f"     TP: ${exit_plan.tp_primary:,.2f}")
            print(f"     R: ${exit_plan.R:,.2f}")
  print(f"     Targets: {len(exit_plan.targets)}")
            print()
        except Exception as e:
            print(f"  ? Exit Plan Failed: {e}")
          import traceback
            traceback.print_exc()
            break
        
        print("STEP 2: Calculate Position Size")
    print("-" * 80)
        
     try:
            qty, notional, margin_used, lev = compute_qty(
                c[i], broker.equity, cfg.get('sizing', {}),
          stop_distance=abs(c[i] - exit_plan.sl),
     atr1h_pct=feat.get('atr1h_pct', [1.0])[i]
 )
            
       print(f"  ? Sizing Calculated:")
print(f"   Quantity: {qty:.6f}")
   print(f"     Notional: ${notional:,.2f}")
            print(f"     Margin: ${margin_used:,.2f}")
   print(f"     Leverage: {lev}x")
          print(f"     Stop Distance: ${abs(c[i] - exit_plan.sl):,.2f}")
            print()
     
            if qty <= 0:
 print(f"  ? QTY IS ZERO! This is why no trade executed.")
                print(f"     Broker equity: ${broker.equity:,.2f}")
           print(f"     Stop distance: ${abs(c[i] - exit_plan.sl):,.2f}")
           print(f"     Config sizing: {cfg.get('sizing', {})}")
   break
         
        except Exception as e:
      print(f"  ? Sizing Failed: {e}")
    import traceback
     traceback.print_exc()
        break
        
        print("STEP 3: Execute Trade")
        print("-" * 80)
      
   try:
         success = broker.open_with_plan(
  ts[i], qty, c[i], lev, exit_plan,
           note=f"{strategy_name}: {signal.get('reason', '')}"
            )
     
            if success:
              print(f"? TRADE EXECUTED!")
  print(f"     Position: {broker.position}")
         else:
      print(f"  ? TRADE FAILED!")
          print(f"   Broker returned False")
            print(f"     Broker has position: {broker.position is not None}")
    print()
            
        except Exception as e:
  print(f"  ? Execution Failed: {e}")
     import traceback
        traceback.print_exc()
   break
        
        # Only test first signal
 break

print("="*80)
print(f"SUMMARY:")
print(f"  Signals tested: {signals_tested}")
print(f"  First signal at bar: {first_signal_bar}")

if signals_tested == 0:
    print("\n? NO SIGNALS FOUND IN SAMPLE!")
else:
    print("\n? Signal ? Execution pipeline tested")
    print(f"   Check output above to see where it failed")
