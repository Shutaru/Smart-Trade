import numpy as np

def ema(arr, n):
    arr = np.asarray(arr, dtype=float)
    if n<=1: return arr.copy()
    alpha = 2/(n+1.0)
    out = np.zeros_like(arr); out[0]=arr[0]
    for i in range(1,len(arr)):
        out[i] = alpha*arr[i] + (1-alpha)*out[i-1]
    return out

def rma(arr, n):
    arr = np.asarray(arr, dtype=float)
    out = np.zeros_like(arr)
    out[min(n-1, len(arr)-1)] = arr[:n].mean() if len(arr)>=n else arr.mean()
    alpha = 1/max(n,1)
    for i in range(n, len(arr)):
        out[i] = alpha*arr[i] + (1-alpha)*out[i-1]
    return out

def atr(high, low, close, n=14):
    high, low, close = map(lambda x: np.asarray(x, dtype=float), (high, low, close))
    tr = np.maximum(high[1:], close[:-1]) - np.minimum(low[1:], close[:-1])
    tr = np.insert(tr, 0, high[0]-low[0])
    return rma(tr, n)

def rsi(close, n=14):
    c = np.asarray(close, dtype=float)
    diff = np.diff(c, prepend=c[0])
    up = np.clip(diff, 0, None); dn = -np.clip(diff, None, 0)
    rs = rma(up, n) / (rma(dn, n) + 1e-12)
    return 100 - (100/(1+rs))

def adx(high, low, close, n=14):
    h, l, c = map(lambda x: np.asarray(x, dtype=float), (high, low, close))
    up = h[1:] - h[:-1]
    dn = l[:-1] - l[1:]
    plusDM = np.where((up>dn) & (up>0), up, 0.0)
    minusDM = np.where((dn>up) & (dn>0), dn, 0.0)
    tr = np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])
    tr = np.insert(tr, 0, h[0]-l[0])
    plusDI = 100 * rma(plusDM, n) / (rma(tr, n)[1:] + 1e-12)
    minusDI = 100 * rma(minusDM, n) / (rma(tr, n)[1:] + 1e-12)
    dx = 100 * np.abs(plusDI - minusDI) / (plusDI + minusDI + 1e-12)
    out = rma(np.insert(dx,0,dx[0]), n)
    return np.concatenate([[out[0]], out])[:len(c)]

def stoch(high, low, close, k=14, d=3):
    h = np.asarray(high, float); l = np.asarray(low, float); c = np.asarray(close, float)
    k_out = np.zeros_like(c)
    for i in range(len(c)):
        i0 = max(0, i-k+1)
        hh = np.max(h[i0:i+1]); ll = np.min(l[i0:i+1]); rng = (hh-ll) if (hh-ll)!=0 else 1e-9
        k_out[i] = 100*((c[i]-ll)/rng)
    d_out = np.convolve(k_out, np.ones(d)/d, mode='same')
    return k_out, d_out

def cci(high, low, close, n=20):
    h = np.asarray(high, float); l = np.asarray(low, float); c = np.asarray(close, float)
    tp = (h+l+c)/3.0
    ma = np.convolve(tp, np.ones(n)/n, mode='same')
    dev = np.zeros_like(tp)
    for i in range(len(tp)):
        i0 = max(0,i-n+1); window = tp[i0:i+1]
        dev[i] = np.mean(np.abs(window - np.mean(window)))
    return (tp - ma) / (0.015*(dev + 1e-12))

def macd(close, fast=12, slow=26, sig=9):
    c = np.asarray(close, float)
    ema_f = ema(c, fast); ema_s = ema(c, slow)
    macd_line = ema_f - ema_s
    signal = ema(macd_line, sig)
    return macd_line, signal, macd_line - signal

def bollinger(close, n=20, k=2.0):
    c = np.asarray(close, float)
    ma = np.convolve(c, np.ones(n)/n, mode='same')
    std = np.zeros_like(c)
    for i in range(len(c)):
        i0 = max(0,i-n+1); std[i] = np.std(c[i0:i+1])
    return ma, ma - k*std, ma + k*std

def donchian(high, low, n=20):
    h = np.asarray(high, float); l = np.asarray(low, float)
    up = np.zeros_like(h); dn = np.zeros_like(l)
    for i in range(len(h)):
        i0 = max(0, i-n+1)
        up[i] = np.max(h[i0:i+1]); dn[i] = np.min(l[i0:i+1])
    return dn, up, (up+dn)/2.0

def keltner(high, low, close, n=20, mult=1.5):
    ema_c = ema(np.asarray(close,float), n)
    atr_v = atr(high, low, close, n)
    return ema_c, ema_c - mult*atr_v, ema_c + mult*atr_v

def supertrend(high, low, close, n=10, mult=3.0):
    h = np.asarray(high, float); l = np.asarray(low, float); c = np.asarray(close, float)
    atr_v = atr(h, l, c, n)
    basic_upper = (h + l)/2.0 + mult*atr_v
    basic_lower = (h + l)/2.0 - mult*atr_v
    final_upper = np.copy(basic_upper)
    final_lower = np.copy(basic_lower)
    st = np.zeros_like(c)
    trend = np.ones_like(c, dtype=int)
    st[0] = final_upper[0]
    for i in range(1, len(c)):
        if c[i] > final_upper[i-1]:
            trend[i] = 1
        elif c[i] < final_lower[i-1]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]
            if trend[i] == 1 and final_lower[i] < st[i-1]:
                final_lower[i] = st[i-1]
            if trend[i] == -1 and final_upper[i] > st[i-1]:
                final_upper[i] = st[i-1]
        st[i] = final_lower[i] if trend[i]==1 else final_upper[i]
    return st, trend  # trend: +1 up, -1 down