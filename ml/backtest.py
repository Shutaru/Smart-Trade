import argparse, os, time, json, numpy as np, pandas as pd, torch
from sklearn.preprocessing import StandardScaler
from core.database import connect, load_range
from core.features import compute_feature_rows
from broker.paper_v1 import PaperFuturesBroker
from core.indicators import supertrend, keltner
from strategies.core import compute_exit_levels
from core.sizing import compute_qty
from ml.model import MLP

def load_model(model_dir="data/ml"):
    import joblib, json
    device = "cuda" if torch.cuda.is_available() else "cpu"
    scaler = joblib.load(os.path.join(model_dir,"scaler.pkl"))
    with open(os.path.join(model_dir,"meta.json"),"r") as f: meta = json.load(f)
    model = MLP(in_dim=len(meta["feat_cols"]), hidden=128, dropout=0.1).to(device)
    model.load_state_dict(torch.load(os.path.join(model_dir,"model.pt"), map_location=device))
    model.eval()
    return model, scaler, meta, device

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=365)
ap.add_argument("--sl-style", type=str, default=None)
ap.add_argument("--breakeven-R", type=float, default=None)
ap.add_argument("--trail-atr", type=float, default=None)
ap.add_argument("--time-stop", type=int, default=None)
ap.add_argument("--p-entry", type=float, default=0.6)
ap.add_argument("--allow-shorts", type=int, default=1)
ap.add_argument("--sl-atr", type=float, default=2.0)
ap.add_argument("--tp-rr", type=float, default=2.0)
ap.add_argument("--equity", type=float, default=100000)
ap.add_argument("--usd", type=float, default=1000)
ap.add_argument("--spread-bps", type=float, default=1.0)
ap.add_argument("--taker-bps", type=float, default=5.0)
ap.add_argument("--maker-bps", type=float, default=2.0)
ap.add_argument("--model-dir", type=str, default="data/ml")
ap.add_argument("--symbol", type=str, default=None)
ap.add_argument("--db", type=str, default=None)
ap.add_argument("--size-mode", type=str, default=None)
ap.add_argument("--usd", type=float, default=None)
ap.add_argument("--portfolio-pct", type=float, default=None)
ap.add_argument("--leverage", type=float, default=None)
ap.add_argument("--progress-file", type=str, default=None)
args = ap.parse_args()

model, scaler, meta, device = load_model(args.model_dir)
import yaml; cfg = yaml.safe_load(open("config.yaml"))
symbol = args.symbol or cfg.get('symbol','BTC/USDT:USDT')
risk = cfg.get('risk', {}).copy()
if args.sl_style: risk['sl_tp_style'] = args.sl_style
if args.sl_atr is not None: risk['sl_atr_mult'] = args.sl_atr
if args.tp_rr is not None: risk['tp_rr_multiple'] = args.tp_rr
if args.breakeven_R is not None: risk['breakeven_at_R'] = args.breakeven_R
if args.trail_atr is not None: risk['trail_atr_mult'] = args.trail_atr
if args.time_stop is not None: risk['time_stop_bars'] = args.time_stop


dbp = args.db or cfg.get('db',{}).get('path','data/bot.db')
conn = connect(dbp)
now = int(time.time()); start = now - args.days*24*60*60
rows = load_range(conn, start, now)
ts = [r[0] for r in rows]; o=[r[1] for r in rows]; h=[r[2] for r in rows]; l=[r[3] for r in rows]; c=[r[4] for r in rows]
feat_rows = compute_feature_rows(ts,o,h,l,c)
# trailing indicators for ML
st_line, st_tr = supertrend(h, l, c, n=10, mult=3.0)
kel_mid, kel_lo, kel_up = keltner(h, l, c, n=20, mult=1.5)

broker = PaperFuturesBroker(equity=args.equity, spread_bps=args.spread_bps, taker_fee_bps=args.taker_bps, maker_fee_bps=args.maker_bps, data_dir='data/ml_bt')
os.makedirs("data/ml_bt", exist_ok=True)
import time; start_t=time.time()
for i, fr in enumerate(feat_rows):
    if args.progress_file and i % 100 == 0:
        elapsed = time.time()-start_t; done=i+1; total=len(feat_rows)
        eta=(total-done)/((done)/(elapsed or 1e-9)) if done>0 else None
        os.makedirs(os.path.dirname(args.progress_file), exist_ok=True)
        open(args.progress_file,"w").write(json.dumps({"total": total, "done": done, "elapsed_sec": elapsed, "eta_sec": eta}))
    # build X
    ema20, ema50, atr14, rsi5, rsi14, bb_mid, bb_lo, bb_up, dn55, up55, regime, macro, atr1h_pct = fr[1],fr[2],fr[3],fr[4],fr[5],fr[7],fr[8],fr[9],fr[10],fr[11],fr[12],fr[13],fr[14]
    close, high, low = c[i], h[i], l[i]
    x = [
        (close-ema20)/close if close else 0.0,
        (close-ema50)/close if close else 0.0,
        rsi5 or 0.0, rsi14 or 0.0,
        fr[6] or 0.0, # adx14
        (close-bb_lo)/((bb_up-bb_lo)+1e-9) if close else 0.0,
        atr14/close*100 if close else 0.0,
        atr1h_pct or 0.0,
        1.0 if regime=='UPTREND' else 0.0,
        1.0 if regime=='DOWNTREND' else 0.0,
        1.0 if regime=='RANGE' else 0.0,
        1.0 if macro=='ABOVE' else (0.0 if macro=='BELOW' else -1.0),
    ]
    x = scaler.transform([x]).astype("float32")
    with torch.no_grad(): prob = torch.sigmoid(model(torch.tensor(x).to(device))).cpu().numpy()[0]
    pL, pS = float(prob[0]), float(prob[1])

    broker.on_candle(ts[i], high, low, close, atr14 or close*0.01, args.spread_bps, args.taker_bps, args.maker_bps, st_line=st_line[i], kel_lo=kel_lo[i], kel_up=kel_up[i])
    if broker.position is None and (pL>=args.p_entry or (args.allow_shorts and pS>=args.p_entry)):
        side = "LONG" if pL>=pS else "SHORT"
        sl_mult, tp_rr = args.sl_atr, args.tp_rr
        if side=="LONG": sl = close - sl_mult*(atr14 or close*0.01); R = close - sl; tp = close + tp_rr*R
        else:            sl = close + sl_mult*(atr14 or close*0.01); R = sl - close; tp = close - tp_rr*R
        from core.sizing import compute_qty
        sizing = cfg.get('sizing',{}).copy()
        if args.size_mode: sizing['mode']=args.size_mode
        if args.usd is not None: sizing['usd']=args.usd
        if args.portfolio_pct is not None: sizing['portfolio_pct']=args.portfolio_pct
        if args.leverage is not None: sizing['leverage']=args.leverage
        qty, notional, margin_used, lev = compute_qty(close, broker.equity, sizing, stop_distance=abs(R))
        if qty>0:
            sl, tp, extra = compute_exit_levels(side, close, atr14 or close*0.01, risk)
            trail_style = 'atr'
            if (risk.get('sl_tp_style') or '').lower()=='supertrend': trail_style='supertrend'
            elif (risk.get('sl_tp_style') or '').lower()=='keltner': trail_style='keltner'
            broker.open(ts[i], side, qty, close, sl, tp, abs(close-sl), cfg.get('sizing',{}).get('leverage',3), args.spread_bps, args.taker_bps, note_extra=f"pL={pL:.2f} pS={pS:.2f}", trailing_style=trail_style, trail_atr_mult=extra.get('trail_atr_mult'), breakeven_at_R=extra.get('breakeven_at_R'))

from core.metrics import equity_metrics, trades_metrics
em = equity_metrics(broker.equity_curve)
tm = trades_metrics(os.path.join("data/ml_bt","trades.csv"))
summary = {**em, **tm}
open(os.path.join("data/ml_bt","summary.json"),"w").write(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))

# --- Generate HTML report for ML BT ---
try:
    import pandas as pd, numpy as np, os, json as js
    outdir = "data/ml_bt"
    eqp = os.path.join(outdir, "equity_curve.csv")
    trp = os.path.join(outdir, "trades.csv")
    eq = pd.read_csv(eqp) if os.path.exists(eqp) else None
    tr = pd.read_csv(trp) if os.path.exists(trp) else None
    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'><title>ML Backtest Report</title><script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script></head><body style='font-family:ui-sans-serif;padding:16px;background:#0b0f1a;color:#e5e7eb'>")
    html.append("<h1>ML Backtest Report</h1><pre style='background:#0f1424;padding:12px;border-radius:8px'>" + json.dumps(summary, indent=2) + "</pre>")
    if eq is not None and len(eq)>0:
        tsx = (eq['ts']*1000).tolist(); y = eq['equity'].tolist()
        html.append("<div id='eq' style='height:320px'></div>")
        html.append(f"<script>Plotly.newPlot('eq',[{{x:{tsx},y:{y},mode:'lines',name:'Equity'}}],{{title:'Equity Curve',margin:{{t:30}}}});</script>")
        cummax = eq['equity'].cummax(); dd = (eq['equity']/cummax - 1.0)*100.0; dd = dd.tolist()
        html.append("<div id='dd' style='height:260px'></div>")
        html.append(f"<script>Plotly.newPlot('dd',[{{x:{tsx},y:{dd},mode:'lines',name:'DD%'}}],{{title:'Drawdown %',margin:{{t:30}}}});</script>")
    if tr is not None and len(tr)>0:
        closed = tr[tr['action'].isin(['TP_FULL','STOP','TIME_STOP','STOP_TRAIL','MANUAL_EXIT','TP_PARTIAL'])]
        pnls = closed['pnl'].fillna(0).tolist()
        html.append("<div id='hist' style='height:260px'></div>")
        html.append(f"<script>Plotly.newPlot('hist',[{{x:{pnls},type:'histogram',nbinsx:60}}],{{title:'PnL por trade',margin:{{t:30}}}});</script>")
    html.append("</body></html>")
    open(os.path.join(outdir, "report.html"), "w", encoding="utf-8").write("\n".join(html))
except Exception as _e:
    pass
