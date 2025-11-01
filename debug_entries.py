"""Quick test to see if there are any valid entries in the data"""
import yaml
import time
from db_sqlite import connect, load_range
from features import compute_feature_rows

cfg = yaml.safe_load(open('config.yaml'))
conn = connect(cfg['db']['path'])
now = int(time.time())
start = now - 90*24*60*60

rows = load_range(conn, start, now)
ts = [r[0] for r in rows]
o = [r[1] for r in rows]
h = [r[2] for r in rows]
l = [r[3] for r in rows]
c = [r[4] for r in rows]
v = [r[5] for r in rows] if len(rows[0]) > 5 else None

feats_rows = compute_feature_rows(ts, o, h, l, c, v)
dn55 = [r[10] for r in feats_rows]
up55 = [r[11] for r in feats_rows]
rsi14 = [r[5] for r in feats_rows]

print(f"Total bars: {len(c)}")
print(f"\nChecking for Donchian breakouts (crosses_above dn55):")

crosses = 0
rsi_below_35 = 0
both_conditions = 0

for i in range(100, len(c)):
    # Check crosses_above
    if c[i-1] <= dn55[i-1] and c[i] > dn55[i]:
        crosses += 1
        if rsi14[i] and rsi14[i] < 35:
            both_conditions += 1
            if both_conditions <= 5:
                print(f"  Bar {i}: close={c[i]:.2f}, dn55={dn55[i]:.2f}, rsi={rsi14[i]:.1f} ✓ LONG SIGNAL")
    
    # Check RSI < 35
    if rsi14[i] and rsi14[i] < 35:
        rsi_below_35 += 1

print(f"\nDonchian crosses_above: {crosses}")
print(f"RSI < 35 occurrences: {rsi_below_35}")
print(f"Both conditions met: {both_conditions}")