import time, numpy as np, pandas as pd
from db_sqlite import connect, load_range
from features import compute_feature_rows

def build_dataset(db_path, days=1460, horizon=12, fee_bps=5.0):
    now = int(time.time()); start = now - days*24*60*60
    conn = connect(db_path); rows = load_range(conn, start, now)
    ts = [r[0] for r in rows]; o=[r[1] for r in rows]; h=[r[2] for r in rows]; l=[r[3] for r in rows]; c=[r[4] for r in rows]
    feats = compute_feature_rows(ts,o,h,l,c)
    import pandas as pd
    df = pd.DataFrame(feats, columns=["ts","ema20","ema50","atr14","rsi5","rsi14","adx14","bb_mid","bb_lo","bb_up","dn55","up55","regime_1h","macro_4h","atr1h_pct"])
    df["c"] = c
    df["ema20_dist"] = (df["c"]-df["ema20"])/df["c"]
    df["ema50_dist"] = (df["c"]-df["ema50"])/df["c"]
    df["bb_pos"] = (df["c"]-df["bb_lo"])/((df["bb_up"]-df["bb_lo"]).abs()+1e-9)
    df["atr_pct_5m"] = df["atr14"]/df["c"]*100
    df["c_fwd"] = df["c"].shift(-horizon)
    df["ret_fwd"] = (df["c_fwd"]-df["c"])/df["c"]
    thr = (fee_bps/10000.0)*2.0
    df["y_long"] = (df["ret_fwd"] > thr).astype(int)
    df["y_short"] = (df["ret_fwd"] < -thr).astype(int)
    regs = df["regime_1h"].map({"UPTREND":[1,0,0],"DOWNTREND":[0,1,0],"RANGE":[0,0,1]}).tolist()
    regs = np.array(regs)
    df["reg_u"], df["reg_d"], df["reg_r"] = regs[:,0], regs[:,1], regs[:,2]
    df["macro_bin"] = df["macro_4h"].map({"ABOVE":1,"BELOW":0}).fillna(-1)
    feat_cols = ["ema20_dist","ema50_dist","rsi5","rsi14","adx14","bb_pos","atr_pct_5m","atr1h_pct","reg_u","reg_d","reg_r","macro_bin"]
    X = df[feat_cols].fillna(0.0).values.astype("float32")
    yL = df["y_long"].fillna(0).values.astype("float32")
    yS = df["y_short"].fillna(0).values.astype("float32")
    n = len(df); n_tr = int(n*0.7)
    return {"feat_cols": feat_cols, "X_train": X[:n_tr], "yL_train": yL[:n_tr], "yS_train": yS[:n_tr],
            "X_oos": X[n_tr:], "yL_oos": yL[n_tr:], "yS_oos": yS[n_tr:], "ts_oos": df["ts"].values[n_tr:]}