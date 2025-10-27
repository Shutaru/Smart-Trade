import pandas as pd, numpy as np, csv, os, json

def equity_metrics(equity_curve):
    if isinstance(equity_curve, str):
        df = pd.read_csv(equity_curve)
        eq = df['equity'].values
    else:
        eq = [e[1] for e in equity_curve]
    if len(eq)<2:
        return {"ret_tot_pct":0,"maxdd_pct":0,"sharpe_ann":0}
    ret = (eq[-1]-eq[0])/eq[0]*100
    peaks = np.maximum.accumulate(eq)
    dd = (eq/peaks - 1.0).min()*100
    # naive sharpe from per-bar equity increments
    rets = np.diff(eq)/eq[:-1]
    if rets.std()==0:
        sharpe = 0.0
    else:
        sharpe = (rets.mean()/rets.std())*np.sqrt(365*24*12)  # ~5m bars/year
    return {"ret_tot_pct": float(ret), "maxdd_pct": float(dd), "sharpe_ann": float(sharpe)}

def trades_metrics(trades_csv):
    if not os.path.exists(trades_csv): return {"trades":0,"win_rate_pct":0,"profit_factor":0}
    df = pd.read_csv(trades_csv)
    closed = df[df['action'].isin(['TP_FULL','STOP','TIME_STOP','STOP_TRAIL','MANUAL_EXIT'])]
    wins = closed[closed['pnl']>0]['pnl'].sum()
    losses = -closed[closed['pnl']<0]['pnl'].sum()
    wr = (closed['pnl']>0).mean()*100 if len(closed)>0 else 0.0
    pf = (wins/max(1e-9, losses)) if losses>0 else (wins if wins>0 else 0.0)
    return {"trades": int(len(closed)), "win_rate_pct": float(wr), "profit_factor": float(pf)}