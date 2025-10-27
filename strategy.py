def compute_exit_levels(side, price, atr5, params, regime_hint=None):
    style = (params.get("sl_tp_style") or "atr_fixed").lower()
    sl_mult = float(params.get("sl_atr_mult", 2.0))
    tp_rr  = float(params.get("tp_rr_multiple", 2.0))
    trail_mult = float(params.get("trail_atr_mult", 2.0))
    if side=="LONG":
        sl = price - sl_mult*(atr5 or price*0.01); R = price - sl; tp = price + tp_rr*R
    else:
        sl = price + sl_mult*(atr5 or price*0.01); R = sl - price; tp = price - tp_rr*R
    extra = {}
    if style == "atr_trailing":
        extra["trail_atr_mult"] = trail_mult
    if style == "chandelier":
        # just reuse trail multiplier
        extra["trail_atr_mult"] = trail_mult
    if style == "breakeven_then_trail":
        extra["breakeven_at_R"] = float(params.get("breakeven_at_R",1.0))
        extra["trail_atr_mult"] = trail_mult
    if style in ("supertrend","keltner"):
        extra["trail_atr_mult"] = trail_mult
    return sl, tp, extra

def should_enter(i, ts, o,h,l,c, feats, params, allow_shorts=True):
    # Simple Donchian breakout + RSI filter + regime bias
    dn55, up55 = feats["dn55"][i], feats["up55"][i]
    rsi14 = feats["rsi14"][i]
    regime = feats["regime"][i]
    long_sig = c[i] > up55 and rsi14 > params.get("rsi_buy", 30) and (regime!="DOWNTREND")
    short_sig = allow_shorts and (c[i] < dn55 and rsi14 < params.get("rsi_sell", 70) and (regime!="UPTREND"))
    if long_sig: return "LONG"
    if short_sig: return "SHORT"
    return None