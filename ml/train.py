import argparse, os, json, numpy as np, torch, torch.nn as nn, torch.optim as optim
from sklearn.preprocessing import StandardScaler
from ml.data import build_dataset
from ml.model import MLP

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=1460)
ap.add_argument("--horizon", type=int, default=12)
ap.add_argument("--hidden", type=int, default=128)
ap.add_argument("--dropout", type=float, default=0.1)
ap.add_argument("--lr", type=float, default=1e-3)
ap.add_argument("--epochs", type=int, default=12)
ap.add_argument("--batch", type=int, default=512)
ap.add_argument("--device", type=str, default="auto")
ap.add_argument("--db", type=str, default="data/bot.db")
ap.add_argument("--progress-file", type=str, default=None)
args = ap.parse_args()

device = "cuda" if (args.device=="auto" and torch.cuda.is_available()) else (args.device if args.device!="auto" else "cpu")
data = build_dataset(args.db, days=args.days, horizon=args.horizon)
scaler = StandardScaler(); Xtr = scaler.fit_transform(data["X_train"]).astype("float32")
model = MLP(in_dim=Xtr.shape[1], hidden=args.hidden, dropout=args.dropout).to(device)
opt = optim.Adam(model.parameters(), lr=args.lr); loss_fn = nn.BCEWithLogitsLoss()

ds = torch.utils.data.TensorDataset(torch.tensor(Xtr, device=device),
                                    torch.tensor(data["yL_train"][:,None], device=device),
                                    torch.tensor(data["yS_train"][:,None], device=device))
dl = torch.utils.data.DataLoader(ds, batch_size=args.batch, shuffle=True)

import time; start=time.time()
for ep in range(args.epochs):
    if args.progress_file:
        import os, json, time as t
        elapsed = t.time()-start; eta = (args.epochs-(ep))/((ep+1)/(elapsed or 1e-9)) if ep>=0 else None
        os.makedirs(os.path.dirname(args.progress_file), exist_ok=True)
        open(args.progress_file,"w").write(json.dumps({"total": args.epochs, "done": ep, "elapsed_sec": elapsed, "eta_sec": eta}))
    model.train(); tot=0.0
    for xb, yL, yS in dl:
        opt.zero_grad(); logits = model(xb)
        loss = loss_fn(logits[:,0:1], yL)+loss_fn(logits[:,1:2], yS); loss.backward(); opt.step(); tot += float(loss.item())

os.makedirs("data/ml", exist_ok=True)
torch.save(model.state_dict(), "data/ml/model.pt")
import joblib; joblib.dump(scaler, "data/ml/scaler.pkl")
with open("data/ml/meta.json","w") as f: json.dump({"feat_cols": data["feat_cols"], "horizon": args.horizon}, f, indent=2)
print("Saved model to data/ml/")