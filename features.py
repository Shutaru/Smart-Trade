import numpy as np, pandas as pd
from indicators import ema, atr, rsi, adx, bollinger, donchian

def resample(ts, o,h,l,c, tf_seconds):
    # assumes 5m base
    df = pd.DataFrame({'ts': ts, 'o':o,'h':h,'l':l,'c':c})
    df['dt'] = pd.to_datetime(df['ts'], unit='s')
    df = df.set_index('dt')
    rule = f'{tf_seconds}s'
    agg = df.resample(rule).agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
    return agg.index.view('int64')//10**9, agg['o'].values, agg['h'].values, agg['l'].values, agg['c'].values

def compute_feature_rows(ts, o, h, l, c):
    ts = np.asarray(ts); o=np.asarray(o); h=np.asarray(h); l=np.asarray(l); c=np.asarray(c)
    ema20_v = ema(c, 20)
    ema50_v = ema(c, 50)
    atr14_v = atr(h, l, c, 14)
    rsi5_v = rsi(c, 5)
    rsi14_v = rsi(c, 14)
    adx14_v = adx(h, l, c, 14)
    bb_mid, bb_lo, bb_up = bollinger(c, 20, 2.0)
    dn55, up55, _ = donchian(h, l, 55)

    # 1h regime via slope of EMA(50)_1h
    ts1h, o1h, h1h, l1h, c1h = resample(ts, o,h,l,c, 3600)
    ema50_1h = ema(c1h, 50)
    slope = np.sign(np.gradient(ema50_1h))
    # map each 5m ts to last 1h slope
    reg = np.where(np.interp(ts, ts1h, slope, left=0, right=0) > 0, "UPTREND", "DOWNTREND")
    # crude range detection: if |c - ema50| < 0.3*ATR(1h) ⇒ RANGE
    atr1h = atr(h1h, l1h, c1h, 14)
    atr1h_pct_1h = atr1h/np.maximum(c1h,1e-9)*100
    dist = np.abs(np.interp(ts, ts1h, ema50_1h, left=ema50_1h[0], right=ema50_1h[-1]) - c)
    rng_flag = (dist < np.interp(ts, ts1h, 0.3*atr1h, left=atr1h[0]*0.3, right=atr1h[-1]*0.3))
    regime = np.where(rng_flag, "RANGE", reg)

    # 4h macro: price above/below EMA200_4h
    ts4h, o4h, h4h, l4h, c4h = resample(ts, o,h,l,c, 14400)
    ema200_4h = ema(c4h, 200)
    macro = np.where(np.interp(ts, ts4h, c4h, left=c4h[0], right=c4h[-1]) >= np.interp(ts, ts4h, ema200_4h, left=ema200_4h[0], right=ema200_4h[-1]), "ABOVE", "BELOW")
    atr1h_pct = np.interp(ts, ts1h, atr1h_pct_1h, left=atr1h_pct_1h[0], right=atr1h_pct_1h[-1])

    rows = []
    for i in range(len(ts)):
        rows.append([int(ts[i]), float(ema20_v[i]), float(ema50_v[i]), float(atr14_v[i]), float(rsi5_v[i]), float(rsi14_v[i]), float(adx14_v[i]), float(bb_mid[i]), float(bb_lo[i]), float(bb_up[i]), float(dn55[i]), float(up55[i]), str(regime[i]), str(macro[i]), float(atr1h_pct[i])])
    return rows