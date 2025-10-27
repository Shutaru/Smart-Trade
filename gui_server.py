# gui_server.py — versão “v12-fix” com aspas escapadas
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

# ============================= Helpers base =============================

app = FastAPI(title="BTC5m Bitget GUI Suite")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def safe_path(p: str) -> str:
    """
    Normaliza e impede path traversal fora do projeto.
    """
    if not p:
        raise HTTPException(400, "path vazio")
    full = os.path.abspath(os.path.join(PROJECT_ROOT, p))
    if not full.startswith(PROJECT_ROOT):
        raise HTTPException(400, "path inválido")
    return full


# -------------------- Job manager (subprocess launcher) -----------------

_JOBS: Dict[str, Dict[str, Any]] = {}


def launch(cmd: str, group: str = "misc", progress: Optional[str] = None) -> Dict[str, Any]:
    """
    Lança um comando no SO como subprocesso. Usa string (shell) para facilitar quotes no Windows.
    Guarda informações básicas numa memória de processo (_JOBS).
    """
    ts = str(int(time.time()))
    job_id = f"{group}_{ts}"
    # Windows: shell=True para expandir string inteira
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
        # Em Windows não é trivial consultar returncode sem reter o Popen.
        # Mantemos “running: True” e, se houver ficheiro de progresso, devolvemos os dados.
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
def api_config_write(cfg: Dict[str, Any] = Body(...)):
    p = safe_path("config.yaml")
    yaml.safe_dump(cfg, open(p, "w", encoding="utf-8"), sort_keys=False)
    return {"ok": True}


# Snapshots (já implementado noutros passos, reexposto aqui)

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

# Backtest (genérico)
@app.post("/api/backtest/run")
def api_backtest_run(days: int = 365):
    # Alguns scripts podem aceitar --days; se não aceitarem, o backtest usa o default interno.
    cmd = f"python backtest.py --days {days}"
    return launch(cmd, "bt")

# Grid Search
@app.post("/api/grid/run")
def api_grid_run(days: int = 365, max_combos: int = 5000, sort: str = "sharpe_ann"):
    # CUIDADO com as aspas: sort vai entre aspas duplas ESCAPADAS
    cmd = f"python gridsearch.py --days {days} --max-combos {max_combos} --sort \\\"{sort}\\\""
    return launch(cmd, "grid")

# Walk-Forward
@app.post("/api/wf/run")
def api_wf_run(days_is: int = 180, days_os: int = 60, folds: int = 6):
    cmd = f"python walkforward.py --is {days_is} --os {days_os} --folds {folds}"
    return launch(cmd, "wf")

# ML backtest (rápido)
@app.post("/api/ml_bt/run")
def api_ml_bt_run(days: int = 365, p_entry: float = 0.6, allow_shorts: int = 1):
    cmd = f"python ml_bt.py --days {days} --p-entry {p_entry} --allow-shorts {allow_shorts}"
    return launch(cmd, "mlbt")

# ML Optuna
@app.post("/api/ml_optuna/run")
def api_ml_optuna_run(n_trials: int = 50, days: int = 365):
    cmd = f"python ml_optuna.py --trials {n_trials} --days {days}"
    return launch(cmd, "mlopt")

# Regime Breakdown (o erro de aspas vinha daqui)
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
    # Avaliador MUITO simples para objective — usa apenas builtins seguros
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


# ============================= Live / Bitget Exec =======================

from executor_bitget import BitgetExecutor  # precisa existir no projeto


@app.get("/api/live/status")
def api_live_status():
    cfg = yaml.safe_load(open("config.yaml", "r"))
    mode = cfg.get("mode", "paper")
    ex = BitgetExecutor(cfg)
    data = {
        "mode": mode,
        "symbol": cfg.get("symbol"),
        "ticker": ex.fetch_ticker(),
        "balance": ex.fetch_balance(),
        "positions": ex.fetch_positions(),
        "orders": ex.fetch_open_orders(),
        "funding": ex.fetch_funding()
    }
    return data


@app.post("/api/live/market")
def api_live_market(side: str, amount: float, reduce_only: int = 0):
    cfg = yaml.safe_load(open("config.yaml", "r"))
    if cfg.get("mode", "paper") != "live":
        raise HTTPException(400, "Está em modo paper.")
    ex = BitgetExecutor(cfg)
    # Risk check (ver abaixo enforce_risk)
    enforce_risk(side, amount, ex.fetch_ticker().get("last") or 0,
                 cfg.get("sizing", {}).get("leverage", 3))
    return ex.market_order(side, amount, bool(reduce_only))


@app.post("/api/live/cancel_all")
def api_live_cancel_all():
    cfg = yaml.safe_load(open("config.yaml", "r"))
    if cfg.get("mode", "paper") != "live":
        raise HTTPException(400, "Está em modo paper.")
    ex = BitgetExecutor(cfg)
    return ex.cancel_all()


@app.post("/api/live/set_leverage")
def api_live_set_leverage(leverage: int = 3, margin_mode: str = "cross"):
    cfg = yaml.safe_load(open("config.yaml", "r"))
    if cfg.get("mode", "paper") != "live":
        raise HTTPException(400, "Está em modo paper.")
    ex = BitgetExecutor(cfg)
    return ex.set_leverage(leverage=leverage, margin_mode=margin_mode)


# --- Risk filter ---
def _risk_cfg():
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    r = cfg.get("risk_limits", {})
    return {
        "max_leverage": float(r.get("max_leverage", 10)),
        "max_order_usd": float(r.get("max_order_usd", 50000)),
        "max_daily_loss_pct": float(r.get("max_daily_loss_pct", 5.0))
    }, cfg


def _price_of_symbol(cfg):
    ex = BitgetExecutor(cfg)
    t = ex.fetch_ticker()
    return t.get("last") or t.get("close") or 0.0


def enforce_risk(side, amount, price, leverage):
    limits, cfg = _risk_cfg()
    px = float(price or _price_of_symbol(cfg) or 0.0)
    notional = abs(float(amount)) * px
    if float(leverage) > limits["max_leverage"]:
        raise HTTPException(400, f"Leverage {leverage} excede max {limits['max_leverage']}")
    if notional > limits["max_order_usd"]:
        raise HTTPException(400, f"Order notional ${notional:.2f} excede max ${limits['max_order_usd']:.2f}")
    return True


@app.post("/api/live/order")
def api_live_order(type: str, side: str, amount: float, price: float = None,
                   stopPrice: float = None, reduce_only: int = 0, post_only: int = 0, leverage: float = None):
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    if cfg.get("mode", "paper") != "live":
        raise HTTPException(400, "Está em modo paper.")
    ex = BitgetExecutor(cfg)
    px = price or (ex.fetch_ticker().get("last") or 0)
    if leverage is None:
        leverage = cfg.get("sizing", {}).get("leverage", 3)
    enforce_risk(side, amount, px, leverage)
    t = type.lower()
    if t == "market":
        return ex.market_order(side, amount, reduce_only=bool(reduce_only))
    elif t == "limit":
        if price is None:
            raise HTTPException(400, "price requerido para limit")
        return ex.limit_order(side, amount, price, reduce_only=bool(reduce_only), post_only=bool(post_only))
    elif t in ("stop", "take_profit", "stop_loss"):
        if stopPrice is None:
            raise HTTPException(400, "stopPrice requerido")
        return ex.stop_order(side, amount, stopPrice, price=price, reduce_only=bool(reduce_only),
                             tp=(t == "take_profit"), sl=(t == "stop_loss"))
    else:
        raise HTTPException(400, "type inválido")


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


@app.get("/api/alerts/tick")
def api_alerts_tick():
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    ex = BitgetExecutor(cfg)
    tick = ex.fetch_ticker() or {}
    last = tick.get("last") or tick.get("close") or 0
    res = []
    for r in _load_alerts().get("rules", []):
        kind, op, val = r.get("kind"), r.get("op"), float(r.get("value", 0))
        ok = False
        if kind == "price":
            x = float(last or 0)
            if op == "gt":
                ok = x > val
            elif op == "lt":
                ok = x < val
        if ok:
            res.append({"kind": kind, "op": op, "value": val, "last": last})
    return {"triggered": res, "last": last}


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


# ============================= Static UI ================================

# Servir a pasta web/ (index.html)
app.mount("/", StaticFiles(directory="web", html=True), name="web")

# === OHLCV do DB para o gráfico (candles) ===
@app.get("/api/candles")
def api_candles(limit: int = 500, timeframe: str = "5m"):
    """
    Lê candles da tua base SQLite definida em config.yaml -> db.path.
    A tabela esperada é 'candles(ts INTEGER, open REAL, high REAL, low REAL, close REAL, volume REAL)'.
    """
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

    # ordenar cronológico crescente (vem desc)
    rows = rows[::-1]
    candles = [{"ts": r[0], "o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4]), "v": float(r[5])} for r in rows]
    return {"symbol": cfg.get("symbol"), "timeframe": timeframe, "candles": candles}

