import argparse, pandas as pd, numpy as np, json, os

ap = argparse.ArgumentParser()
ap.add_argument("--trades", type=str, required=True)
ap.add_argument("--outdir", type=str, required=True)
ap.add_argument("--progress-file", type=str, default=None)
args = ap.parse_args()

os.makedirs(args.outdir, exist_ok=True)
df = pd.read_csv(args.trades)
# placeholder: aggregate by action
summary = df.groupby("action")["pnl"].agg(["count","sum","mean"]).reset_index()
summary.to_csv(os.path.join(args.outdir,"regime_summary.csv"), index=False)
print(json.dumps({"outdir": args.outdir, "rows": len(summary)}, indent=2))