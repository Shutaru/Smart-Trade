def compute_qty(price, equity, sizing_cfg, stop_distance=None, atr1h_pct=None):
    mode = sizing_cfg.get("mode", "usd")
    lev  = float(sizing_cfg.get("leverage", 3))
    max_util = float(sizing_cfg.get("max_margin_util_pct", 80))/100.0
    if mode == "usd":
        notional = float(sizing_cfg.get("usd", 1000))
    else:
        notional = equity * float(sizing_cfg.get("portfolio_pct", 0.01)) / 100.0
    notional = min(notional, equity*lev*max_util)
    qty = max(0.0, notional/price)
    margin_used = notional/lev
    return qty, notional, margin_used, lev