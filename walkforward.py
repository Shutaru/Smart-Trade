import argparse, os, time, json, yaml, pandas as pd, numpy as np, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("--total-days", type=int, default=730)
ap.add_argument("--is-days", type=int, default=120)
ap.add_argument("--oos-days", type=int, default=30)
ap.add_argument("--step-days", type=int, default=30)
ap.add_argument("--max-combos", type=int, default=40)
ap.add_argument("--progress-file", type=str, default=None)
args = ap.parse_args()

with open("config.yaml","r") as f: base_cfg = yaml.safe_load(f)
stamp = int(time.time())
outdir = os.path.join("data","wf", str(stamp)); os.makedirs(outdir, exist_ok=True)

runs = []
start_t = time.time()
steps = max(1, (args.total_days - (args.is_days + args.oos_days)) // args.step_days + 1)
for k in range(steps):
    if args.progress_file:
        elapsed = time.time()-start_t
        done = k; total = steps
        eta = (total-done)/((done)/(elapsed or 1e-9)) if done>0 else None
        os.makedirs(os.path.dirname(args.progress_file), exist_ok=True)
        with open(args.progress_file, "w") as pf:
            pf.write(json.dumps({"total": total, "done": done, "elapsed_sec": elapsed, "eta_sec": eta}))

    # run a gridsearch limited for this window by adjusting --days to IS
    cmd = [sys.executable, "gridsearch.py", "--days", str(args.is_days), "--max-combos", str(args.max_combos)]
    out = subprocess.check_output(cmd, text=True)
    # pick best by sharpe
    import json as js, glob, pandas as pd
    gdirs = sorted(glob.glob("data/grid/*"), key=os.path.getmtime, reverse=True)
    grid_dir = gdirs[0]
    df = pd.read_csv(os.path.join(grid_dir,"top_by_sharpe_ann.csv"))
    best = df.iloc[0].to_dict()
    # apply best params to config
    cfg = dict(base_cfg); cfg["risk"].update({k:best[k] for k in best if k in cfg["risk"]})
    with open("config.yaml","w") as f: yaml.safe_dump(cfg, f, sort_keys=False)
    # backtest OOS
    out2 = subprocess.check_output([sys.executable, "backtest.py", "--days", str(args.oos_days)], text=True)
    # collect equity
    import json as js2
    lines = [l for l in out2.splitlines() if l.strip().startswith('{')]
    summ = js2.loads(lines[-1]) if lines else {}
    runs.append(summ)

# combine OOS equity of last backtest dir
import glob
bdirs = sorted(glob.glob("data/backtests/*"), key=os.path.getmtime, reverse=True)
eqs = []
for d in bdirs[:steps]:
    p = os.path.join(d, "equity_curve.csv")
    if os.path.exists(p):
        eqs.append(pd.read_csv(p))
oos = pd.concat(eqs).sort_values("ts")
oos.to_csv(os.path.join(outdir,"wf_oos_equity.csv"), index=False)
with open(os.path.join(outdir,"wf_summary.json"),"w") as f:
    json.dump({"runs": len(runs), "oos_mean_sharpe": float(np.mean([r.get("sharpe_ann",0) for r in runs])),
               "oos_mean_ret_pct": float(np.mean([r.get("ret_tot_pct",0) for r in runs])),
               "oos_mean_maxdd_pct": float(np.mean([r.get("maxdd_pct",0) for r in runs]))}, f, indent=2)
print(json.dumps({"outdir": outdir, "runs": len(runs)}, indent=2))

# HTML report
try:
    rep = os.path.join(outdir, "report.html")
    import pandas as pd, json as js
    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'><title>WF Report</title><script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script></head><body style='font-family:ui-sans-serif;padding:16px;background:#0b0f1a;color:#e5e7eb'>")
    html.append("<h1>Walk-Forward Report</h1>")
    summ = js.load(open(os.path.join(outdir,"wf_summary.json"))) if os.path.exists(os.path.join(outdir,"wf_summary.json")) else {}
    html.append(f"<pre style='background:#0f1424;padding:12px;border-radius:8px'>{json.dumps(summ, indent=2)}</pre>")
    eqp = os.path.join(outdir, "wf_oos_equity.csv")
    if os.path.exists(eqp):
        df = pd.read_csv(eqp); tsx = (df['ts']*1000).tolist(); y = df['equity'].tolist()
        html.append("<div id='oos' style='height:320px'></div>")
        html.append(f"<script>Plotly.newPlot('oos',[{{x:{tsx},y:{y},mode:'lines',name:'OOS Equity'}}],{{title:'WF OOS Equity',margin:{{t:30}}}});</script>")
    html.append("</body></html>")
    open(rep,"w",encoding="utf-8").write("\n".join(html))
except Exception as _e:
    pass
