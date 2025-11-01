import pandas as pd, numpy as np, csv, os, json

def equity_metrics(equity_curve):
    if isinstance(equity_curve, str):
        df = pd.read_csv(equity_curve)
        eq = df['equity'].values
    else:
        eq = [e[1] for e in equity_curve]
    
    if len(eq) < 2:
        return {"ret_tot_pct": 0, "maxdd_pct": 0, "sharpe_ann": 0}
    
    # Total return
    ret = (eq[-1] - eq[0]) / eq[0] * 100
    
    # Drawdown
    peaks = np.maximum.accumulate(eq)
    dd = (eq / peaks - 1.0).min() * 100
    
    # FIXED: More robust Sharpe calculation
    # Convert equity to returns
    rets = np.diff(eq) / eq[:-1]
    
    if len(rets) < 2:
        sharpe = 0.0
    elif rets.std() == 0 or np.isnan(rets.std()):
        # Zero volatility or NaN ? set Sharpe to 0
        sharpe = 0.0
    else:
        # Calculate Sharpe ratio from returns
        mean_ret = rets.mean()
        std_ret = rets.std()
    
        # Annualization factor for 5-minute bars
        # 288 bars per day (24h * 60min / 5min)
        bars_per_day = 288
        bars_per_year = bars_per_day * 365
        
        # Sharpe ratio (risk-free rate = 0)
        sharpe_per_bar = mean_ret / std_ret
        
        # Annualize using square root of time
        sharpe = sharpe_per_bar * np.sqrt(bars_per_year)
   
        # Cap extreme values (likely due to small sample)
        if len(rets) < 100:
            # Small sample: cap Sharpe at 10
            sharpe = min(sharpe, 10.0)
        
        # Sanity check: if return is small but Sharpe is huge, cap it
        if abs(ret) < 5.0 and abs(sharpe) > 10.0:
            # Less than 5% return but Sharpe > 10? Likely artifact
            sharpe = min(sharpe, ret / 0.5)  # Rough approximation
    
    return {
        "ret_tot_pct": float(ret),
        "maxdd_pct": float(dd),
        "sharpe_ann": float(sharpe)
    }

def trades_metrics(trades_csv):
    if not os.path.exists(trades_csv):
        return {"trades": 0, "win_rate_pct": 0, "profit_factor": 0}
    
    df = pd.read_csv(trades_csv)
    closed = df[df['action'].isin(['TP_FULL', 'STOP', 'TIME_STOP', 'STOP_TRAIL', 'MANUAL_EXIT'])]
    
    wins = closed[closed['pnl'] > 0]['pnl'].sum()
    losses = -closed[closed['pnl'] < 0]['pnl'].sum()
    wr = (closed['pnl'] > 0).mean() * 100 if len(closed) > 0 else 0.0
    pf = (wins / max(1e-9, losses)) if losses > 0 else (wins if wins > 0 else 0.0)
    
    return {
        "trades": int(len(closed)),
        "win_rate_pct": float(wr),
        "profit_factor": float(pf)
    }