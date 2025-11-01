import numpy as np, pandas as pd
from .indicators import ema, atr, rsi, adx, bollinger, donchian, macd, stoch, cci, supertrend, mfi, vwap, obv, keltner

def resample(ts, o,h,l,c, tf_seconds):
    # assumes 5m base
    df = pd.DataFrame({'ts': ts, 'o':o,'h':h,'l':l,'c':c})
    df['dt'] = pd.to_datetime(df['ts'], unit='s')
    df = df.set_index('dt')
    rule = f'{tf_seconds}s'
    agg = df.resample(rule).agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
    return agg.index.view('int64')//10**9, agg['o'].values, agg['h'].values, agg['l'].values, agg['c'].values

def compute_feature_rows(ts, o, h, l, c, v=None):
    """
    Compute all technical indicators and return feature rows
    
    Args:
 ts: timestamps
    o, h, l, c: OHLC data
        v: volume (optional, will use dummy values if not provided)
    
    Returns:
        List of feature rows with all indicators
    """
    ts = np.asarray(ts); o=np.asarray(o); h=np.asarray(h); l=np.asarray(l); c=np.asarray(c)
    
    # Handle volume (use dummy if not provided for backward compatibility)
    if v is None:
        v = np.ones_like(c) * 1000.0  # Dummy volume
    else:
        v = np.asarray(v)
    
    # Basic indicators (no volume needed)
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

    # Additional indicators
    macd_line, macd_signal, macd_hist = macd(c,12,26,9)
    stoch_k_v, stoch_d_v = stoch(h, l, c,14,3)
    cci20_v = cci(h, l, c,20)
    # Williams %R (period14)
    williams_r_v = np.zeros_like(c)
    per =14
    for i in range(len(c)):
        i0 = max(0, i-per+1)
        hh = np.max(h[i0:i+1])
        ll = np.min(l[i0:i+1])
        rng = hh - ll if (hh - ll) !=0 else 1e-9
        williams_r_v[i] = -100.0 * (hh - c[i]) / rng

    # SuperTrend
    st_line_v, st_dir_v = supertrend(h, l, c, n=10, mult=3.0)
    
    # Volume-based indicators (NEW!)
    mfi14_v = mfi(h, l, c, v, 14)
    vwap_v = vwap(h, l, c, v)
    obv_v = obv(c, v)
    
    # Keltner Channels
    kel_mid_v, kel_lo_v, kel_up_v = keltner(h, l, c, n=20, mult=2.0)

    rows = []
    for i in range(len(ts)):
        rows.append([
        int(ts[i]),
        float(ema20_v[i]),
        float(ema50_v[i]),
        float(atr14_v[i]),
        float(rsi5_v[i]),
        float(rsi14_v[i]),
        float(adx14_v[i]),
        float(bb_mid[i]),
        float(bb_lo[i]),
        float(bb_up[i]),
        float(dn55[i]),
        float(up55[i]),
        str(regime[i]),
        str(macro[i]),
        float(atr1h_pct[i]),
        float(macd_line[i]),
        float(macd_signal[i]),
        float(macd_hist[i]),
        float(stoch_k_v[i]),
        float(stoch_d_v[i]),
        float(cci20_v[i]),
        float(williams_r_v[i]),
        float(st_line_v[i]),
        int(st_dir_v[i]),
        float(mfi14_v[i]),      # NEW: index 24
        float(vwap_v[i]),       # NEW: index 25
        float(obv_v[i]), # NEW: index 26
        float(kel_mid_v[i]),  # NEW: index 27
        float(kel_lo_v[i]),     # NEW: index 28
        float(kel_up_v[i])  # NEW: index 29
  ])
    return rows