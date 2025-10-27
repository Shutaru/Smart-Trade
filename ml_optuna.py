import argparse, os, json, optuna, torch, time
import yaml, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=1460)
ap.add_argument("--trials", type=int, default=40)
ap.add_argument("--study", type=str, default="ml_search")
ap.add_argument("--outdir", type=str, default=None)
ap.add_argument("--progress-file", type=str, default=None)
args = ap.parse_args()

with open("config.yaml","r") as f: cfg = yaml.safe_load(f)
db_path = cfg.get("db",{}).get("path","data/bot.db")

start = time.time()
def objective(trial):
    import random
    import random
    device = f"cuda:{trial.number % torch.cuda.device_count()}" if torch.cuda.is_available() else "cpu"
    horizon = trial.suggest_int("horizon", 6, 36)
    hidden = trial.suggest_categorical("hidden", [64,128,256])
    dropout = trial.suggest_float("dropout", 0.0, 0.3)
    lr = trial.suggest_float("lr", 1e-4, 3e-3, log=True)
    epochs = trial.suggest_int("epochs", 6, 18)
    batch = trial.suggest_categorical("batch", [256,512,1024])
    p_entry = trial.suggest_float('p_entry', 0.55, 0.75)
    sl_style = trial.suggest_categorical('sl_style', ['atr_fixed','atr_trailing','chandelier','supertrend','keltner','breakeven_then_trail'])
    sl_atr = trial.suggest_float('sl_atr', 1.0, 3.5)
    tp_rr = trial.suggest_float('tp_rr', 1.2, 3.5)
    breakeven_R = trial.suggest_float('breakeven_R', 0.5, 1.5)
    trail_atr = trial.suggest_float('trail_atr', 1.0, 3.0)
    time_stop = trial.suggest_int('time_stop', 48, 192)
    allow_shorts = trial.suggest_categorical('allow_shorts', [0,1])
    size_mode = trial.suggest_categorical('size_mode', ['usd','portfolio_pct'])
    usd_amt = trial.suggest_float('usd_amt', 500, 5000)
    port_pct = trial.suggest_float('portfolio_pct', 0.2, 3.0)
    leverage = trial.suggest_int('leverage', 1, 10)
    # train
    subprocess.check_call([sys.executable, "ml_train.py", "--days", str(args.days), "--horizon", str(horizon), "--hidden", str(hidden), "--dropout", str(dropout), "--lr", str(lr), "--epochs", str(epochs), "--batch", str(batch), "--device", device])
    # backtest OOS (~1/3)
    out = subprocess.check_output([sys.executable, 'ml_bt.py', '--days', str(args.days//3), '--p-entry', str(p_entry), '--allow-shorts', str(allow_shorts), '--sl-style', str(sl_style), '--sl-atr', str(sl_atr), '--tp-rr', str(tp_rr), '--breakeven-R', str(breakeven_R), '--trail-atr', str(trail_atr), '--time-stop', str(time_stop), '--size-mode', str(size_mode), '--usd', str(usd_amt), '--portfolio-pct', str(port_pct), '--leverage', str(leverage)], text=True)
    import json as js
    lines = [l for l in out.splitlines() if l.strip().startswith('{')]
    metrics = js.loads(lines[-1]) if lines else {}
    trial.set_user_attr("metrics", metrics)
    return float(metrics.get("sharpe_ann",0.0))

def cb(study, trial):
    if args.progress_file:
        done = len(study.trials); elapsed = time.time()-start
        eta = (args.trials-done)/((done)/(elapsed or 1e-9)) if done>0 else None
        os.makedirs(os.path.dirname(args.progress_file), exist_ok=True)
        open(args.progress_file,"w").write(json.dumps({"total": args.trials, "done": done, "elapsed_sec": elapsed, "eta_sec": eta, "best": study.best_value if study.best_trial else None}))

storage = f"sqlite:///data/{args.study}.db"
os.makedirs("data", exist_ok=True)
study = optuna.create_study(direction="maximize", study_name=args.study, storage=storage, load_if_exists=True)
study.optimize(objective, n_trials=args.trials, n_jobs=min(args.trials, 4), callbacks=[cb])
print("Best value (Sharpe):", study.best_value)
print("Best params:", json.dumps(study.best_params, indent=2))

# Save trials and HTML report
import pandas as pd, time, json as js
stamp = int(time.time()); outdir = args.outdir or os.path.join('data','ml_optuna', str(stamp))
os.makedirs(outdir, exist_ok=True)
recs = []
for t in study.trials:
    m = t.user_attrs.get('metrics', {})
    row = {'number': t.number, 'value': t.value, **(m or {}), **t.params}
    recs.append(row)
df = pd.DataFrame(recs)
df.to_csv(os.path.join(outdir,'trials.csv'), index=False)

# HTML
html = []
html.append("<!doctype html><html><head><meta charset='utf-8'><title>ML Optuna Report</title><script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script></head><body style='font-family:ui-sans-serif;padding:16px;background:#0b0f1a;color:#e5e7eb'>")
html.append("<h1>ML Optuna Report</h1>")
if len(df)>0:
    y = df['value'].fillna(0).tolist(); x = list(range(len(y)))
    html.append("<div id='best' style='height:320px'></div>")
    html.append(f"<script>var y={y};var x={x};var best=[];var b=-1e9;for(var i=0;i<y.length;i++){b=Math.max(b,y[i]);best.push(b)};Plotly.newPlot('best',[{x:x,y:y,mode:'markers',name:'trial value'},{x:x,y:best,mode:'lines',name:'best so far'}],{title:'Objective (Sharpe) por trial',margin:{t:30}});</script>")
    html.append("<h2>Top 20</h2>")
    html.append(df.sort_values(by='value', ascending=False).head(20).to_html(index=False))
open(os.path.join(outdir,'report.html'),'w',encoding='utf-8').write("\n".join(html))
print(json.dumps({'outdir': outdir, 'trials': len(df)}, indent=2))
