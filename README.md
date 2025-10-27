# BTC 5m Futures — Bitget GUI (v7)

Tudo para correr **local** (Windows/Linux) com **GUI**, **paper/live**, **Grid/WF**, **ML (GPU)**, **LLM Co‑Pilot**, dashboards, ETAs e muito mais.

## 🚀 Instalação
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows
# source .venv/bin/activate        # Linux/Mac
pip install -r requirements.txt
uvicorn gui_server:app --host 127.0.0.1 --port 8000 --reload
# abre: http://localhost:8000
```

## 📂 Estrutura
- `gui_server.py` — FastAPI (endpoints + arrancar jobs + ETAs + LLM via Ollama)
- `web/` — GUI moderna com dashboards
- `config.yaml` — modo, sizing, fees, risco, ML, **tuning ranges**
- `backtest.py` / `gridsearch.py` / `walkforward.py`
- `ml_train.py` / `ml_bt.py` / `ml_optuna.py`
- `indicators.py` / `features.py` / `sizing.py` / `broker_futures_paper.py` / `metrics.py`
- `executor_bitget.py` — stub de integração LIVE (Bitget, via ccxt)

## 🧭 Paper vs Live
Escolhe no GUI **Modo persistente** (grava em `config.yaml`). O botão **Flatten (panic)** fecha posições (LIVE).

## 🔧 Tuning & Estratégia
- Indicadores extra: **Stochastic/CCI/MACD/Supertrend/Keltner**, além de EMA/RSI/ADX/BB/Donchian/ATR.
- SL/TP styles: `atr_fixed`, `atr_trailing`, `chandelier`, `supertrend`, `keltner`, `breakeven_then_trail`.
- Ranges em `config.yaml:tuning`.

## 🤖 ML (GPU + Optuna)
- `ml_train.py` treina MLP (P(subida), P(descida)) usando features 5m + regimes.
- `ml_bt.py` faz backtest sobre as probabilidades (com SL/TP em ATR).
- `ml_optuna.py` usa TODAS as GPUs (se houver) e maximiza **Sharpe** OOS (~1/3).

## ⏱️ Progresso e ETA
Todos os jobs escrevem `data/progress/job_*.json` com `{total, done, elapsed_sec, eta_sec}`. O GUI mostra barras com **ETA**.

## 📈 Dashboards & Pareto
- Equity & Drawdown, histograma PnL, OOS equity (WF), leaderboard (Grid), heatmap PnL, overlay equity+trades.

## 🔒 Notas
- Chaves no GUI são mascaradas; patchs LLM criam backup `.bak`.
- Recomendo correres com **dados preenchidos** (candles 5m) via `db_sqlite` + backfill (tu adicionas as tuas credenciais Bitget e backfill por `ccxt`).

Boa sorte e bons trades! 🟢

## 📄 Relatório HTML
Cada backtest gera `report.html` na pasta da run (equity, DD, KPIs, histograma PnL e heatmap DOW×HOUR).


## 🔗 Bitget — Pares & Backfill
No GUI podes listar pares USDT Perp da Bitget e fazer backfill 5m on‑demand para um DB por par (`data/db/<PAR>_5m.db`). Depois basta carregar "Usar no config".


## 📘 ML Optuna Report
Cada corrida grava `data/ml_optuna/<ts>/trials.csv` e `report.html` (best‑so‑far, top 20 e parâmetros).


## 🧩 Snapshots de config
Cria snapshots do `config.yaml` e faz rollback pelo GUI.


## 🟢 Live Monitor
Painel em tempo‑real (modo **live**) com preço, posições, ordens, funding e controlos: Buy/Sell MKT (reduce‑only), Set Leverage, Cancel All e Flatten.


## 📦 Perfis de Estratégia
Exporta/Importa/Aplica perfis (risk, sizing, fees, ml, symbol/db) a partir do GUI, com snapshots e rollback.


## 📘 ML Backtest Report
Cada `ml_bt.py` gera `data/ml_bt/report.html` com Equity/Drawdown/Histograma de PnL.



## ⚙️ Risk Limits (config.yaml)
```yaml
risk_limits:
  max_leverage: 10
  max_order_usd: 50000
  max_daily_loss_pct: 5.0
```
Ordens live respeitam estes limites (bloqueadas se excederem).

## 🔌 Live WebSocket
- Botão **WS Start** no Live Monitor liga ao `/ws/price` que subscreve o **Bitget WS** (ticker). Fallback por polling continua disponível.

## 🧾 Tipos de Ordem (Live)
- **Market**, **Limit** (post-only opcional), **Stop**, **Take Profit**, **Stop Loss** (com `stopPrice`).
- Flag **reduce-only** disponível.

## 🔔 Alertas
- Regras simples (ex.: preço `>` valor), com **som** opcional.
