"""
Analyze BTC market conditions in the last 90 days
Check if market was ranging (low ADX) or trending (high ADX)
"""

import yaml
import time
from core.database import connect, load_range
from core.features import compute_feature_rows

# Load config
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

# Load last 90 days
conn = connect(cfg['db']['path'])
now = int(time.time())
start = now - 90 * 24 * 60 * 60

rows = load_range(conn, start, now)
ts = [r[0] for r in rows]
o = [r[1] for r in rows]
h = [r[2] for r in rows]
l = [r[3] for r in rows]
c = [r[4] for r in rows]
v = [r[5] for r in rows] if len(rows[0]) > 5 else None

print(f"Analyzing BTC market (last 90 days)")
print(f"Total candles: {len(rows)}")
print(f"Period: {time.strftime('%Y-%m-%d', time.localtime(start))} to {time.strftime('%Y-%m-%d', time.localtime(now))}")
print("\n" + "="*80)

# Calculate features
feats_rows = compute_feature_rows(ts, o, h, l, c, v)

adx_values = [r[6] for r in feats_rows if r[6] is not None]
regime_values = [r[12] for r in feats_rows if r[12] is not None]

# Statistics
print("\nADX ANALYSIS:")
print(f"  Average ADX: {sum(adx_values)/len(adx_values):.2f}")
print(f"  Min ADX: {min(adx_values):.2f}")
print(f"  Max ADX: {max(adx_values):.2f}")
print(f"  Median ADX: {sorted(adx_values)[len(adx_values)//2]:.2f}")

# Count bars by ADX level
adx_below_18 = sum(1 for x in adx_values if x < 18)
adx_18_to_22 = sum(1 for x in adx_values if 18 <= x < 22)
adx_22_to_25 = sum(1 for x in adx_values if 22 <= x < 25)
adx_above_25 = sum(1 for x in adx_values if x >= 25)

total = len(adx_values)

print("\nADX DISTRIBUTION:")
print(f"  ADX < 18 (weak/no trend):{adx_below_18:6d} bars ({adx_below_18/total*100:5.1f}%)")
print(f"  ADX 18-22 (emerging):      {adx_18_to_22:6d} bars ({adx_18_to_22/total*100:5.1f}%)")
print(f"  ADX 22-25 (trend):      {adx_22_to_25:6d} bars ({adx_22_to_25/total*100:5.1f}%)")
print(f"  ADX > 25 (strong trend):   {adx_above_25:6d} bars ({adx_above_25/total*100:5.1f}%)")

print("\n" + "="*80)
print("\nREGIME ANALYSIS:")

from collections import Counter
regime_counts = Counter(regime_values)

for regime, count in regime_counts.most_common():
    print(f"  {regime:15s}: {count:6d} bars ({count/len(regime_values)*100:5.1f}%)")

print("\n" + "="*80)
print("\nCONCLUSION:")

avg_adx = sum(adx_values)/len(adx_values)

if avg_adx < 18:
    print("  Market was in RANGING mode (ADX < 18)")
    print("  Trend-following strategies will struggle.")
    print("  Mean reversion strategies should work better.")
elif avg_adx < 22:
    print("  Market was in WEAK TREND mode (ADX 18-22)")
    print("  Trend strategies need ADX >= 22, hence 0 trades.")
elif avg_adx < 25:
    print("  Market was in MODERATE TREND mode (ADX 22-25)")
    print("  Trend strategies should have some trades.")
else:
    print("  Market was in STRONG TREND mode (ADX > 25)")
    print("  Trend strategies should work well.")

print("\n" + "="*80)
print("\nRECOMMENDATION:")

if avg_adx < 20:
    print("  Option 1: Test with a different period (when BTC was trending)")
    print("  Option 2: Reduce ADX threshold from 22 to 18 in trend strategies")
    print("  Option 3: Test with WLFI or another volatile altcoin")
else:
    print("  Market conditions were adequate for trending.")
    print("  Issue might be in strategy logic or other filters.")

print()
