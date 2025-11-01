import argparse, os, time, json, itertools, random, csv, yaml
from backtest import np, compute_feature_rows, PaperFuturesBroker, connect, load_range  # reuse imports via backtest
from core.metrics import equity_metrics, trades_metrics

def build_param_grid(cfg):
    tun = (cfg or {}).get('tuning', {})
    keys = list(tun.keys()); vals = [tun[k] for k in keys]
    combos = [dict(zip(keys, v)) for v in itertools.product(*vals)] if keys else [{}]
    random.shuffle(combos)
    return combos

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--max-combos", type=int, default=60)
    ap.add_argument("--sort", type=str, default="sharpe_ann,-maxdd_pct,ret_tot_pct")
    ap.add_argument("--progress-file", type=str, default=None)
    args = ap.parse_args()

    with open("config.yaml","r") as f: cfg = yaml.safe_load(f)
    combos = build_param_grid(cfg)[:args.max_combos]

    start = time.time()
    rows = []
    outdir = os.path.join("data","grid", str(int(time.time())))
    os.makedirs(outdir, exist_ok=True)

    for i, params in enumerate(combos):
        # write progress
        if args.progress_file:
            elapsed = time.time()-start
            eta = (len(combos)-(i+1))/(((i+1))/(elapsed or 1e-9)) if i>=0 else None
            os.makedirs(os.path.dirname(args.progress_file), exist_ok=True)
            with open(args.progress_file,"w") as pf:
                pf.write(json.dumps({"total": len(combos), "done": i+1, "elapsed_sec": elapsed, "eta_sec": eta}))

        # run a backtest quickly by tweaking cfg risk with current params
        import copy, subprocess, sys, json as js
        tmp_cfg = copy.deepcopy(cfg); tmp_cfg["risk"].update(params)
        tmp_cfg_path = os.path.join(outdir, f"cfg_{i}.yaml")
        with open(tmp_cfg_path,"w") as f: yaml.safe_dump(tmp_cfg, f)
        # call backtest with same DB/days but using this temp cfg (hack: env var)
        env = os.environ.copy(); env["BT_CFG"] = tmp_cfg_path
        cmd = [sys.executable, "-c", "import os,yaml,backtest,json; cfgp=os.environ['BT_CFG']; import shutil; shutil.copyfile(cfgp,'config.yaml'); import sys; sys.argv=['backtest.py','--days',str(%d)]; import runpy; runpy.run_module('backtest', run_name='__main__')" % args.days]
        out = subprocess.check_output(cmd, text=True, env=env)
        lines = [l for l in out.splitlines() if l.strip().startswith('{')]
        metrics = js.loads(lines[-1]) if lines else {}
        rows.append({**params, **metrics})

    # save CSV
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(outdir,"grid_results.csv"), index=False)
    # quick tops
    for col, asc in [("sharpe_ann", False), ("win_rate_pct", False), ("ret_tot_pct", False), ("profit_factor", False), ("maxdd_pct", True)]:
        s = df.sort_values(by=col, ascending=asc).head(50)
        s.to_csv(os.path.join(outdir, f"top_by_{col}.csv"), index=False)
    print(json.dumps({"outdir": outdir, "n": len(df)}, indent=2))

# HTML report
try:
    import pandas as pd, numpy as np
    rep = os.path.join(outdir, "report.html")
    df = pd.read_csv(os.path.join(outdir,"grid_results.csv"))
    topS = df.sort_values(by="sharpe_ann", ascending=False).head(50)
    topP = df.sort_values(by="profit_factor", ascending=False).head(50)
    sharpe = df["sharpe_ann"].fillna(0).tolist()
    maxdd = df["maxdd_pct"].abs().fillna(0).tolist()
    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'><title>Grid Report</title><script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script></head><body style='font-family:ui-sans-serif;padding:16px;background:#0b0f1a;color:#e5e7eb'>")
    html.append("<h1>Grid Search Report</h1>")
    html.append("<div id='pareto' style='height:360px'></div>")
    html.append(f"<script>Plotly.newPlot('pareto',[{{x:{maxdd},y:{sharpe},mode:'markers',name:'combos'}}],{{title:'Sharpe vs MaxDD',xaxis:{{title:'MaxDD %'}},yaxis:{{title:'Sharpe'}}}});</script>")
    html.append("<h2>Top 50 por Sharpe</h2>"); html.append(topS.head(50).to_html(index=False))
    html.append("<h2>Top 50 por Profit Factor</h2>"); html.append(topP.head(50).to_html(index=False))
    html.append("</body></html>")
    open(rep,"w",encoding="utf-8").write("\n".join(html))
except Exception as _e:
    pass
