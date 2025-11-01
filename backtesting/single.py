import argparse, time, os, json, csv, re, sys
import yaml
import numpy as np
from db_sqlite import connect, load_range
from features import compute_feature_rows
from indicators import supertrend, keltner
from broker_futures_paper import PaperFuturesBroker
from sizing import compute_qty
from strategy import should_enter, compute_exit_levels
from metrics import equity_metrics, trades_metrics

# Support compact argument form like `--days30` (user typed no space).
# Transform sys.argv in-place for patterns like --nameVALUE -> --name VALUE
def _preprocess_argv():
    argv = sys.argv
    new_argv = [argv[0]]
    # Pattern captures a flag name followed immediately by digits, e.g. --days30
    # Ensure the name group does not eat trailing digit characters by making it non-greedy
    pattern = re.compile(r"^--([a-zA-Z_][a-zA-Z0-9_-]*?)(\d+)$")
    for a in argv[1:]:
        m = pattern.match(a)
        if m:
            name = m.group(1)
            val = m.group(2)
            new_argv.append(f"--{name}")
            new_argv.append(val)
        else:
            new_argv.append(a)
    sys.argv[:] = new_argv

_preprocess_argv()

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=365)
ap.add_argument("--progress-file", type=str, default=None)
ap.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
args = ap.parse_args()

with open(args.config,"r") as f: cfg = yaml.safe_load(f)
conn = connect(cfg.get("db",{}).get("path","data/bot.db"))
now = int(time.time()); start = now - args.days*24*60*60
rows = load_range(conn, start, now)
ts = [r[0] for r in rows]; o=[r[1] for r in rows]; h=[r[2] for r in rows]; l=[r[3] for r in rows]; c=[r[4] for r in rows]
v = [r[5] for r in rows] if len(rows[0]) > 5 else None  # Extract volume if available

feats_rows = compute_feature_rows(ts,o,h,l,c,v)
# indicators for trailing
st_line, st_tr = supertrend(h, l, c, n=10, mult=3.0)
kel_mid, kel_lo, kel_up = keltner(h, l, c, n=20, mult=1.5)
# columns mapping
feat = {
    "ema20": [r[1] for r in feats_rows],
    "ema50": [r[2] for r in feats_rows],
    "atr14": [r[3] for r in feats_rows],
    "rsi5": [r[4] for r in feats_rows],
    "rsi14": [r[5] for r in feats_rows],
    "adx14": [r[6] for r in feats_rows],
    "bb_mid": [r[7] for r in feats_rows],
    "bb_lo": [r[8] for r in feats_rows],
    "bb_up": [r[9] for r in feats_rows],
    "dn55": [r[10] for r in feats_rows],
    "up55": [r[11] for r in feats_rows],
  "regime": [r[12] for r in feats_rows],
    "macro": [r[13] for r in feats_rows],
    "atr1h_pct": [r[14] for r in feats_rows],
    # additional indicators
    "macd": [r[15] for r in feats_rows],
    "macd_signal": [r[16] for r in feats_rows],
  "macd_hist": [r[17] for r in feats_rows],
    "stoch_k": [r[18] for r in feats_rows],
    "stoch_d": [r[19] for r in feats_rows],
    "cci20": [r[20] for r in feats_rows],
    "williams_r": [r[21] for r in feats_rows],
    "supertrend": [r[22] for r in feats_rows],
    "supertrend_dir": [r[23] for r in feats_rows],
    # NEW: Volume-based indicators
    "mfi14": [r[24] for r in feats_rows],
    "vwap": [r[25] for r in feats_rows],
    "obv": [r[26] for r in feats_rows],
    "keltner_mid": [r[27] for r in feats_rows],
    "keltner_lo": [r[28] for r in feats_rows],
    "keltner_up": [r[29] for r in feats_rows],
}

outdir = os.path.join("data","backtests", str(int(time.time())))
os.makedirs(outdir, exist_ok=True)
broker = PaperFuturesBroker(
    equity=float(cfg.get("account",{}).get("starting_equity_usd",100000)),
    max_daily_loss_pct=float(cfg.get("risk",{}).get("max_daily_loss_pct",2.0)),
    partial_tp_at_R=float(cfg.get("risk",{}).get("partial_tp_at_R",1.0)),
    trail_atr_mult=float(cfg.get("risk",{}).get("trail_atr_mult",2.0)),
    time_stop_bars=int(cfg.get("risk",{}).get("time_stop_bars",96)),
    spread_bps=float(cfg.get("fees",{}).get("spread_bps",1.0)),
    taker_fee_bps=float(cfg.get("fees",{}).get("taker_fee_bps",5.0)),
    maker_fee_bps=float(cfg.get("fees",{}).get("maker_fee_bps",2.0)),
    data_dir=outdir
)

start_t = time.time()
for i in range(len(ts)):
    if args.progress_file and i % 100 == 0:
        elapsed = time.time()-start_t
        done = i+1; total = len(ts)
        eta = (total-done)/((done)/(elapsed or 1e-9)) if done>0 else None
        os.makedirs(os.path.dirname(args.progress_file), exist_ok=True)
        with open(args.progress_file, "w") as pf:
            pf.write(json.dumps({"total": total, "done": done, "elapsed_sec": elapsed, "eta_sec": eta}))

    atr5 = feat["atr14"][i] or (c[i]*0.01)
    broker.on_candle(ts[i], h[i], l[i], c[i], atr5, cfg['fees']['spread_bps'], cfg['fees']['taker_fee_bps'], cfg['fees']['maker_fee_bps'], st_line=st_line[i], kel_lo=kel_lo[i], kel_up=kel_up[i])

    if broker.position is None:
        side = should_enter(i, ts, o,h,l,c, feat, cfg.get("risk",{}), allow_shorts=cfg.get("risk",{}).get("allow_shorts",True))
        if side:
            sl, tp, extra = compute_exit_levels(side, c[i], atr5, cfg.get('risk',{}), feat['regime'][i])
            trail_style = 'atr'
            if cfg.get('risk',{}).get('sl_tp_style')=='supertrend': trail_style='supertrend'
            elif cfg.get('risk',{}).get('sl_tp_style')=='keltner': trail_style='keltner'
            qty, notional, margin_used, lev = compute_qty(c[i], broker.equity, cfg.get('sizing',{}), stop_distance=abs(c[i]-sl), atr1h_pct=feat['atr1h_pct'][i])
            if qty>0:
                broker.open(ts[i], side, qty, c[i], sl, tp, abs(c[i]-sl), lev, cfg['fees']['spread_bps'], cfg['fees']['taker_fee_bps'], note_extra=f"regime={feat['regime'][i]} macro={feat['macro'][i]}", trailing_style=trail_style, trail_atr_mult=extra.get('trail_atr_mult'), breakeven_at_R=extra.get('breakeven_at_R'))

# metrics
em = equity_metrics(broker.equity_curve)
tm = trades_metrics(os.path.join(outdir,"trades.csv"))
summary = {**em, **tm, "outdir": outdir}
with open(os.path.join(outdir,"summary.json"),"w") as f: json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))

# --- Generate HTML report ---
try:
    import pandas as pd, numpy as np
    eqp = os.path.join(outdir, "equity_curve.csv")
    trp = os.path.join(outdir, "trades.csv")
    eq = pd.read_csv(eqp) if os.path.exists(eqp) else None
    tr = pd.read_csv(trp) if os.path.exists(trp) else None
    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'><title>Backtest Report</title><script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script></head><body style='font-family:ui-sans-serif;padding:16px;background:#0b0f1a;color:#e5e7eb'>")
    html.append(f"<h1>Backtest Report</h1><pre style='background:#0f1424;padding:12px;border-radius:8px'>{json.dumps(summary, indent=2)}</pre>")
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
        dt = pd.to_datetime(tr['ts_utc'], unit='s', errors='coerce')
        tr['dow'] = dt.dt.dayofweek; tr['hour'] = dt.dt.hour
        pv = tr.pivot_table(index='dow', columns='hour', values='pnl', aggfunc='sum', fill_value=0.0)
        z = pv.values.tolist(); xs = [int(c) for c in pv.columns.tolist()]; ys = [int(i) for i in pv.index.tolist()]
        html.append("<div id='heat' style='height:360px'></div>")
        html.append(f"<script>Plotly.newPlot('heat',[{{z:{z},x:{xs},y:{ys},type:'heatmap',colorbar:{{title:'PnL'}}}}],{{title:'PnL Heatmap (DiaSemana×Hora)'}});</script>")
    html.append("</body></html>")
    open(os.path.join(outdir, "report.html"), "w", encoding="utf-8").write("\n".join(html))
except Exception as _e:
    pass
