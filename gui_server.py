# gui_server.py
import os
import sys
import time
import json
import yaml
import asyncio
import subprocess
from typing import Dict, Any, Optional

import websockets
from fastapi import FastAPI, HTTPException, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="BTC5m Bitget GUI Suite")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Registrar router do Strategy Lab
from routers.lab import router as lab_router
app.include_router(lab_router)


def safe_path(p: str) -> str:
    """Normaliza e impede path traversal fora do projeto"""
    if not p:
        raise HTTPException(400, "path vazio")
    full = os.path.abspath(os.path.join(PROJECT_ROOT, p))
    if not full.startswith(PROJECT_ROOT):
        raise HTTPException(400, "path inválido")
    return full


# -------------------- Job manager (subprocess launcher) -----------------

_JOBS: Dict[str, Dict[str, Any]] = {}


def launch(cmd: str, group: str = "misc", progress: Optional[str] = None) -> Dict[str, Any]:
    """Lança um comando no SO como subprocesso"""
    ts = str(int(time.time()))
    job_id = f"{group}_{ts}"
    popen = subprocess.Popen(cmd, shell=True, cwd=PROJECT_ROOT)
    _JOBS[job_id] = {
        "id": job_id,
        "group": group,
        "cmd": cmd,
        "pid": popen.pid,
        "started": int(time.time()),
        "progress": progress,
    }
    return {"job_id": job_id, "pid": popen.pid, "cmd": cmd, "progress": progress}


@app.get("/api/jobs/list")
def api_jobs_list():
    return {"jobs": list(_JOBS.values())}


@app.get("/api/jobs/status")
def api_jobs_status(job_id: str):
    j = _JOBS.get(job_id)
    if not j:
        raise HTTPException(404, "job não encontrado")
    status = {"running": True, "returncode": None}
    try:
        if j.get("progress") and os.path.exists(j["progress"]):
            try:
                status["progress_json"] = json.loads(open(j["progress"], "r", encoding="utf-8").read() or "{}")
            except Exception:
                pass
    except Exception:
        pass
    return {"job": j, "status": status}


# ============================= Config I/O ===============================

@app.get("/api/config/read")
def api_config_read():
    p = safe_path("config.yaml")
    if not os.path.exists(p):
        raise HTTPException(404, "config.yaml não encontrado")
    return yaml.safe_load(open(p, "r", encoding="utf-8"))


@app.post("/api/config/write")
def api_config_write(cfg: Dict[str, Any] = Body(...)
):
    p = safe_path("config.yaml")
    yaml.safe_dump(cfg, open(p, "w", encoding="utf-8"), sort_keys=False)
    return {"ok": True}


@app.post("/api/config/snapshot")
def api_cfg_snapshot():
    stamp = int(time.time())
    os.makedirs(os.path.join("data", "config_snapshots"), exist_ok=True)
    dst = os.path.join("data", "config_snapshots", f"config_{stamp}.yaml")
    import shutil
    shutil.copyfile("config.yaml", dst)
    return {"ok": True, "path": dst}


@app.get("/api/config/snapshots")
def api_cfg_snapshots():
    base = os.path.join("data", "config_snapshots")
    out = []
    if os.path.exists(base):
        for fn in os.listdir(base):
            p = os.path.join(base, fn)
            if os.path.isfile(p):
                out.append({"path": p, "mtime": os.stat(p).st_mtime})
    return {"snapshots": sorted(out, key=lambda x: x["mtime"], reverse=True)}


@app.post("/api/config/rollback")
def api_cfg_rollback(path: str):
    p = safe_path(path)
    if not os.path.exists(p):
        raise HTTPException(404, "snapshot não encontrado")
    import shutil
    shutil.copyfile(p, "config.yaml")
    return {"ok": True, "restored": path}


# ============================= Execuções ===============================

@app.post("/api/backtest/run")
def api_backtest_run(days: int = 365):
    cmd = f"python backtest.py --days {days}"
    return launch(cmd, "bt")


@app.post("/api/grid/run")
def api_grid_run(days: int = 365, max_combos: int = 5000, sort: str = "sharpe_ann"):
    cmd = f"python gridsearch.py --days {days} --max-combos {max_combos} --sort \\\"{sort}\\\""
    return launch(cmd, "grid")


@app.post("/api/wf/run")
def api_wf_run(days_is: int = 180, days_os: int = 60, folds: int = 6):
    cmd = f"python walkforward.py --is {days_is} --os {days_os} --folds {folds}"
    return launch(cmd, "wf")


@app.post("/api/ml_bt/run")
def api_ml_bt_run(days: int = 365, p_entry: float = 0.6, allow_shorts: int = 1):
    cmd = f"python ml_bt.py --days {days} --p-entry {p_entry} --allow-shorts {allow_shorts}"
    return launch(cmd, "mlbt")


@app.post("/api/ml_optuna/run")
def api_ml_optuna_run(n_trials: int = 50, days: int = 365):
    cmd = f"python ml_optuna.py --trials {n_trials} --days {days}"
    return launch(cmd, "mlopt")


@app.post("/api/rb/run")
def api_regime_breakdown(trades_path: str, outdir: str):
    tp = safe_path(trades_path)
    od = safe_path(outdir)
    cmd = f"python regime_breakdown.py --trades \\\"{tp}\\\" --outdir \\\"{od}\\\""
    return launch(cmd, "rb")


# ============================= Grid: Pareto & Apply ====================

@app.get("/api/grid/pareto")
def api_grid_pareto(base_path: str):
    import pandas as pd
    p = safe_path(base_path)
    fn = os.path.join(p, "grid_results.csv")
    if not os.path.exists(fn):
        raise HTTPException(404, "grid_results.csv não encontrado")
    df = pd.read_csv(fn)
    df = df.dropna(subset=["sharpe_ann", "maxdd_pct"])
    pts = [{
        "sharpe": float(r["sharpe_ann"]),
        "maxdd": float(abs(r["maxdd_pct"])),
        "params": {k: r[k] for k in df.columns if k not in ["sharpe_ann", "maxdd_pct"]}
    } for _, r in df.iterrows()]
    return {"points": pts[:5000]}


@app.post("/api/grid/apply_best")
def api_grid_apply_best(base_path: str, metric: str = "sharpe_ann", ascending: int = 0):
    import pandas as pd
    p = safe_path(base_path)
    fn = os.path.join(p, "grid_results.csv")
    if not os.path.exists(fn):
        raise HTTPException(404, "grid_results.csv não encontrado")
    df = pd.read_csv(fn)
    if metric not in df.columns:
        raise HTTPException(400, "métrica inválida")
    df2 = df.sort_values(by=metric, ascending=bool(ascending)).head(1)
    if len(df2) == 0:
        raise HTTPException(400, "sem linhas")
    best = df2.iloc[0].to_dict()
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    risk = cfg.get("risk", {})
    changed = []
    for k, v in best.items():
        if k in risk and isinstance(v, (int, float, str, bool)):
            risk[k] = v
            changed.append(k)
    cfg["risk"] = risk
    yaml.safe_dump(cfg, open("config.yaml", "w", encoding="utf-8"), sort_keys=False)
    return {"ok": True, "applied_keys": changed, "metric": metric, "value": best.get(metric)}


def safe_eval(expr: str, vars_dict: Dict[str, Any]) -> Any:
    allowed_names = {"__builtins__": {"abs": abs, "max": max, "min": min, "float": float}}
    return eval(expr, allowed_names, vars_dict)


@app.post("/api/grid/apply_objective")
def api_grid_apply_objective(base_path: str, days: int = 365,
                             formula: str = "sharpe_ann - max(0,(maxdd_pct-20)/10)",
                             min_trades_per_week: float = 0.0, max_dd: float = 1000.0, min_sharpe: float = -1000.0):
    import pandas as pd
    import numpy as np
    p = safe_path(base_path)
    fn = os.path.join(p, "grid_results.csv")
    if not os.path.exists(fn):
        raise HTTPException(404, "grid_results.csv não encontrado")
    df = pd.read_csv(fn)
    if "trades" not in df.columns:
        df["trades"] = 0
    df["trades_per_week"] = df["trades"] / max(1.0, days / 7.0)
    m = (df["trades_per_week"] >= min_trades_per_week) & (df["maxdd_pct"].abs() <= abs(max_dd)) & (df["sharpe_ann"] >= min_sharpe)
    df2 = df[m].copy()
    scores = []
    for _, row in df2.iterrows():
        v = {k: float(row[k]) if k in row else 0.0 for k in
             ["sharpe_ann", "maxdd_pct", "ret_tot_pct", "win_rate_pct", "profit_factor", "trades", "trades_per_week"]}
        try:
            s = float(safe_eval(formula, v))
        except Exception:
            s = float("nan")
        scores.append(s)
    df2["objective"] = scores
    df2 = df2.replace([np.inf, -np.inf], np.nan).dropna(subset=["objective"]).sort_values(by="objective", ascending=False)
    if len(df2) == 0:
        raise HTTPException(400, "sem candidatos após filtros")
    best = df2.iloc[0].to_dict()
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    risk = cfg.get("risk", {})
    changed = []
    for k, v in best.items():
        if k in risk and isinstance(v, (int, float, str, bool)):
            risk[k] = v
            changed.append(k)
    cfg["risk"] = risk
    yaml.safe_dump(cfg, open("config.yaml", "w", encoding="utf-8"), sort_keys=False)
    return {"ok": True, "applied_keys": changed, "objective": best.get("objective"), "row": best}


# ============================= Bitget / DB ==============================

@app.get("/api/bitget/pairs")
def api_pairs():
    import ccxt
    ex = ccxt.bitget({"options": {"defaultType": "swap"}})
    ms = ex.load_markets()
    syms = [s for s, m in ms.items() if (":USDT" in s or "/USDT:" in s) and (m.get("type") == "swap" or "swap" in (m.get("info") or {}).get("support", "swap"))]
    syms = sorted(list(set(syms)))
    return {"symbols": syms}


@app.post("/api/bitget/backfill")
def api_backfill(symbol: str, days: int = 1460, timeframe: str = "5m"):
    sym_san = symbol.replace("/", "_").replace(":", "_")
    dbp = os.path.join("data", "db", f"{sym_san}_{timeframe}.db")
    os.makedirs(os.path.dirname(dbp), exist_ok=True)
    cmd = f"python bitget_backfill.py --symbol \\\"{symbol}\\\" --days {days} --timeframe {timeframe} --db \\\"{dbp}\\\""
    return launch(cmd, "bfill")


@app.post("/api/config/set_symbol_db")
def api_set_symbol_db(symbol: str, db_path: str):
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    cfg["symbol"] = symbol
    cfg["db"] = {"path": db_path}
    yaml.safe_dump(cfg, open("config.yaml", "w", encoding="utf-8"), sort_keys=False)
    return {"ok": True, "symbol": symbol, "db_path": db_path}


# ============================= Perfis (export/import/apply) =============

@app.post("/api/profile/export")
def api_profile_export(name: str = "default"):
    stamp = int(time.time())
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    profile = {
        "version": 1,
        "created": stamp,
        "name": name,
        "config": {
            "symbol": cfg.get("symbol"),
            "timeframe": cfg.get("timeframe", "5m") if "timeframe" in cfg else "5m",
            "db": cfg.get("db", {}),
            "fees": cfg.get("fees", {}),
            "sizing": cfg.get("sizing", {}),
            "risk": cfg.get("risk", {}),
            "ml": cfg.get("ml", {})
        }
    }
    os.makedirs("data/profiles", exist_ok=True)
    path = os.path.join("data/profiles", f"profile_{name}_{stamp}.yaml")
    yaml.safe_dump(profile, open(path, "w", encoding="utf-8"), sort_keys=False)
    return {"ok": True, "path": path}


@app.get("/api/profile/list")
def api_profile_list():
    base = "data/profiles"
    out = []
    if os.path.exists(base):
        for fn in os.listdir(base):
            if fn.endswith(".yaml"):
                p = os.path.join(base, fn)
                st = os.stat(p)
                out.append({"path": p, "mtime": st.st_mtime, "name": fn})
    return {"profiles": sorted(out, key=lambda x: x["mtime"], reverse=True)}


@app.post("/api/profile/apply")
def api_profile_apply(path: str):
    p = safe_path(path)
    data = yaml.safe_load(open(p, "r", encoding="utf-8"))
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    for k in ["symbol", "db", "fees", "sizing", "risk", "ml"]:
        if k in data.get("config", {}):
            cfg[k] = data["config"][k]
    yaml.safe_dump(cfg, open("config.yaml", "w", encoding="utf-8"), sort_keys=False)
    return {"ok": True, "applied": ["symbol", "db", "fees", "sizing", "risk", "ml"]}


@app.post("/api/profile/import_text")
def api_profile_import_text(text: str = Body(..., embed=True)):
    obj = yaml.safe_load(text)
    if not isinstance(obj, dict) or "config" not in obj:
        raise HTTPException(400, "Conteúdo inválido.")
    stamp = int(time.time())
    os.makedirs("data/profiles", exist_ok=True)
    path = os.path.join("data/profiles", f"profile_import_{stamp}.yaml")
    open(path, "w", encoding="utf-8").write(text)
    return {"ok": True, "path": path}


# ============================= Alertas ==================================

ALERTS_PATH = os.path.join("data", "alerts.json")


def _load_alerts():
    if os.path.exists(ALERTS_PATH):
        try:
            return json.load(open(ALERTS_PATH, "r", encoding="utf-8"))
        except Exception:
            return {"rules": []}
    return {"rules": []}


def _save_alerts(obj):
    os.makedirs(os.path.dirname(ALERTS_PATH), exist_ok=True)
    json.dump(obj, open(ALERTS_PATH, "w", encoding="utf-8"))


@app.get("/api/alerts/list")
def api_alerts_list():
    return _load_alerts()


@app.post("/api/alerts/add")
def api_alerts_add(kind: str, op: str, value: float):
    a = _load_alerts()
    a["rules"].append({"kind": kind, "op": op, "value": value})
    _save_alerts(a)
    return {"ok": True, "rules": a["rules"]}


@app.post("/api/alerts/clear")
def api_alerts_clear():
    _save_alerts({"rules": []})
    return {"ok": True}


# ============================= Runs list ================================

@app.get("/api/runs/list")
def api_runs_list():
    def _list(base):
        p = safe_path(base)
        if not os.path.exists(p):
            return []
        xs = []
        for d in os.listdir(p):
            full = os.path.join(p, d)
            if os.path.isdir(full):
                xs.append({"path": full, "mtime": os.stat(full).st_mtime, "name": d})
        return sorted(xs, key=lambda x: x["mtime"], reverse=True)

    return {
        "backtest": _list(os.path.join("data", "backtest")),
        "grid": _list(os.path.join("data", "grid")),
        "wf": _list(os.path.join("data", "wf")),
        "ml_bt": _list(os.path.join("data", "ml_bt")),
        "ml_optuna": _list(os.path.join("data", "ml_optuna")),
    }


# ============================= Account Equity (Live/Paper) ==============

@app.get("/api/account/equity")
async def get_account_equity(mode: str = "paper"):
    """
    Get equity curve for live or paper trading account
    
    Args:
        mode: 'live' or 'paper' (default: paper)
    
    Returns:
      {"equity": [{"ts": 1716153600000, "equity": 10000.0}]}
    """
    
    if mode not in ["live", "paper"]:
        raise HTTPException(400, f"Invalid mode: {mode}. Must be 'live' or 'paper'")
    
    # Determine data directory based on mode
    data_dir = os.path.join("data", mode)
    equity_path = os.path.join(data_dir, "equity_curve.csv")
    
    # Return empty if no data
    if not os.path.exists(equity_path):
        return {"equity": []}
    
    # Read equity curve from CSV
    import csv
    equity_data = []
    
    try:
        with open(equity_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert timestamp to milliseconds if in seconds
                ts = int(row['ts'])
                if ts < 9999999999:  # Unix seconds (10 digits)
                    ts = ts * 1000  # Convert to milliseconds
                
                equity_data.append({
                    'ts': ts,
                    'equity': float(row['equity'])
                })
    
    except Exception as e:
        print(f"[API] Error reading equity curve: {e}")
        return {"equity": []}
    
    return {"equity": equity_data}


@app.get("/api/live/equity_curve")
async def get_live_equity_curve():
    """Get equity curve for live trading account"""
    result = await get_account_equity(mode="live")
    return {"curve": result["equity"]}


@app.get("/api/paper/equity_curve")
async def get_paper_equity_curve():
    """Get equity curve for paper trading account"""
    result = await get_account_equity(mode="paper")
    return {"curve": result["equity"]}


@app.get("/api/live/status")
async def get_live_status():
    """Get live trading account status"""
    
    data_dir = "data/live"
    equity_path = os.path.join(data_dir, "equity_curve.csv")
    trades_path = os.path.join(data_dir, "trades.csv")
    
    # Default values
    status = {
        "total_balance": 0.0,
        "today_income": 0.0,
        "daily_change_perc": 0.0,
        "equity": 0.0,
        "start_equity": 100000.0,
        "total_trades": 0,
        "win_rate": 0.0
    }
    
    # Read equity
    if os.path.exists(equity_path):
        try:
            import pandas as pd
            df = pd.read_csv(equity_path)
            if len(df) > 0:
                status["equity"] = float(df.iloc[-1]['equity'])
                status["start_equity"] = float(df.iloc[0]['equity'])
                status["total_balance"] = status["equity"]
   
                # Calculate today's change (if we have data from today)
                if len(df) > 1:
                    prev_equity = float(df.iloc[-2]['equity'])
                    status["today_income"] = status["equity"] - prev_equity
                    status["daily_change_perc"] = (status["today_income"] / prev_equity) * 100
        except Exception as e:
            print(f"[API] Error reading live equity: {e}")
    
    # Read trades
    if os.path.exists(trades_path):
        try:
            import pandas as pd
            df = pd.read_csv(trades_path)
            
            # Count completed trades
            completed = df[df['action'].isin(['TP_FULL', 'STOP', 'TIME_STOP', 'STOP_TRAIL', 'MANUAL_EXIT'])]
            status["total_trades"] = len(completed)
     
            # Calculate win rate
            if len(completed) > 0:
                wins = len(completed[completed['pnl'] > 0])
                status["win_rate"] = (wins / len(completed)) * 100
        
        except Exception as e:
            print(f"[API] Error reading live trades: {e}")
    
    return status


@app.get("/api/paper/status")
async def get_paper_status():
    """Get paper trading account status"""
    
    data_dir = "data/paper"
    equity_path = os.path.join(data_dir, "equity_curve.csv")
    trades_path = os.path.join(data_dir, "trades.csv")
    
    # Default values
    status = {
        "equity": 100000.0,
        "start_equity": 100000.0,
        "total_trades": 0,
        "win_rate": 0.0
    }
    
    # Read equity
    if os.path.exists(equity_path):
        try:
            import pandas as pd
            df = pd.read_csv(equity_path)
            if len(df) > 0:
                status["equity"] = float(df.iloc[-1]['equity'])
                status["start_equity"] = float(df.iloc[0]['equity'])
        except Exception as e:
            print(f"[API] Error reading paper equity: {e}")
    
    # Read trades
    if os.path.exists(trades_path):
        try:
            import pandas as pd
            df = pd.read_csv(trades_path)
    
            # Count completed trades
            completed = df[df['action'].isin(['TP_FULL', 'STOP', 'TIME_STOP', 'STOP_TRAIL', 'MANUAL_EXIT'])]
            status["total_trades"] = len(completed)
            
            # Calculate win rate
            if len(completed) > 0:
                wins = len(completed[completed['pnl'] > 0])
                status["win_rate"] = (wins / len(completed)) * 100
        
        except Exception as e:
            print(f"[API] Error reading paper trades: {e}")
    
    return status


# === OHLCV do DB para o gráfico (candles) ===
@app.get("/api/candles")
def api_candles(limit: int = 500, timeframe: str = "5m"):
    import sqlite3
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    dbp = cfg.get("db", {}).get("path")
    if not dbp:
        raise HTTPException(400, "db.path não definido no config.yaml")
    if not os.path.exists(dbp):
        raise HTTPException(404, f"Base de dados não existe: {dbp}")

    conn = sqlite3.connect(dbp)
    cur = conn.cursor()
    cur.execute("SELECT ts, open, high, low, close, volume FROM candles ORDER BY ts DESC LIMIT ?", (int(limit),))
    rows = cur.fetchall()
    conn.close()

    rows = rows[::-1]
    candles = [{"ts": r[0], "o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4]), "v": float(r[5])} for r in rows]
    return {"symbol": cfg.get("symbol"), "timeframe": timeframe, "candles": candles}


# ============================= WS de preço ==============================

class PriceStreamer:
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.last: Dict[str, Any] = {}
        self.clients = set()
        self.symbol: Optional[str] = None

    async def _run(self, symbol: str):
        url = "wss://ws.bitget.com/mix/v1/stream"
        sub = {"op": "subscribe", "args": [{"instType": "mc", "channel": "ticker", "instId": symbol}]}
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                await ws.send(json.dumps(sub))
                while True:
                    msg = await ws.recv()
                    try:
                        data = json.loads(msg)
                        self.last = {"ts": int(time.time()), "raw": data}
                        price = None
                        if isinstance(data, dict):
                            price = data.get("data", [{}])[0].get("last", "") if isinstance(data.get("data", None), list) else None
                        payload = json.dumps({"t": self.last["ts"], "p": price})
                        for c in list(self.clients):
                            try:
                                await c.send_text(payload)
                            except Exception:
                                self.clients.discard(c)
                    except Exception:
                        pass
        except Exception:
            await asyncio.sleep(2.0)

    def start(self, symbol: str):
        self.symbol = symbol
        if self.task and not self.task.done():
            return
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._run(symbol))


price_streamer = PriceStreamer()


@app.websocket("/ws/price")
async def ws_price(ws: WebSocket):
    await ws.accept()
    price_streamer.clients.add(ws)
    try:
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        price_streamer.clients.discard(ws)


@app.post("/api/ws/start")
def api_ws_start():
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    sym = cfg.get("symbol", "BTC/USDT:USDT")
    price_streamer.start(sym)
    return {"ok": True, "symbol": sym}


# ============================= WS Lab Run Progress ======================

@app.websocket("/ws/lab/run/{run_id}")
async def ws_lab_run(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for real-time run progress and logs"""
    await websocket.accept()
    
    from lab_runner import subscribe_ws, unsubscribe_ws, get_run_status
    
    status = get_run_status(run_id)
    if not status:
        await websocket.send_json({"error": "Run not found", "run_id": run_id})
        await websocket.close()
        return
    
    subscribe_ws(run_id, websocket)
    
    await websocket.send_json({
        "ts": int(time.time() * 1000),
        "level": "INFO",
        "msg": f"Connected to run {run_id[:8]}...",
        "progress": status['progress'],
        "best_score": status.get('best_score'),
        "status": status['status']
    })
    
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        unsubscribe_ws(run_id, websocket)
    except Exception as e:
        print(f"[WS] Error in lab run websocket: {e}")
        unsubscribe_ws(run_id, websocket)


# === Static UI (React SPA em webapp/dist) ===
from pathlib import Path

DIST = Path(__file__).parent / "webapp" / "dist"

if DIST.exists():
    assets_dir = DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    print(f"[UI] Serving static assets from: {assets_dir}")
else:
    print(f"[UI] WARNING: webapp/dist not found at {DIST}")
    print(f"[UI] Run 'npm run build' in webapp/ to build the frontend")


@app.get("/", include_in_schema=False)
async def spa_index():
    """Serve React SPA index.html"""
    index_path = DIST / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=503,
            detail="UI build not found; run `npm run build` in webapp/"
        )
    return FileResponse(str(index_path))


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_catch_all(full_path: str):
    """
    SPA fallback for client-side routing
    
    Serves index.html for all routes except:
    - /api/* (API endpoints)
    - /ws/* (WebSocket endpoints)
    - /assets/* (static files, already mounted)
    """
    # Don't intercept API or WebSocket routes
    if full_path.startswith("api/") or full_path.startswith("ws/"):
        raise HTTPException(status_code=404, detail=f"Endpoint not found: /{full_path}")
    
    # Try to serve direct file if it exists (e.g., favicon.ico, robots.txt)
    file_path = DIST / full_path
    if file_path.is_file() and file_path.exists():
        return FileResponse(str(file_path))
    
    # Fallback to index.html for client-side routing
    index_path = DIST / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=503,
            detail="UI build not found; run `npm run build` in webapp/"
        )
 
    return FileResponse(str(index_path))


# Configure lab_runner with main event loop
@app.on_event("startup")
async def startup_event():
    """Set the main event loop for lab_runner WebSocket broadcasting"""
    from lab_runner import set_main_loop
    loop = asyncio.get_event_loop()
    set_main_loop(loop)
    
    print("[Startup] Configured lab_runner with main event loop")
    print(f"[Startup] DIST directory: {DIST}")
    print(f"[Startup] DIST exists: {DIST.exists()}")
    
    if DIST.exists():
        index_path = DIST / "index.html"
        if index_path.exists():
            print(f"[Startup] ✅ React SPA ready to serve")
            print(f"[Startup] Access at: http://localhost:8000")
        else:
            print(f"[Startup] ⚠️  index.html not found in dist/")
    else:
        print(f"[Startup] ⚠️  React SPA not built")
        print(f"[Startup] Run: cd webapp && npm run build")