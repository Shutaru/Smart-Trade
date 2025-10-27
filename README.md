# Smart Trade Terminal (v13-Pro)

Uma stack completa para trading de futuros BTC/USDT a 5 minutos com backend FastAPI e uma nova SPA React (Vite + TypeScript + Tailwind + shadcn/ui). O objetivo é oferecer uma experiência "Smart Terminal" moderna no estilo 3Commas/Lovable, com execução paper/live, laboratórios de estratégia e gestão de dados/configuração.

> **Nota**: `config.yaml` não deve ser versionado; utilize `config.example.yaml` como referência e mantenha as suas chaves/API em segurança.

## ✨ Principais Módulos

### Backend FastAPI
- Endpoints para execução paper/live (Bitget via CCXT), gestão de risco e monitorização de conta.
- Jobs longos: backtest, grid search, walk-forward, Optuna + ML pipeline.
- WebSocket de preço em tempo real (`/ws/price`).
- Servidor estático da SPA gerada em `webapp/dist`, com fallback para `index.html`.

### Frontend React (webapp/)
- React + Vite + TypeScript + Tailwind + shadcn/ui + lucide-react.
- Layout persistente com Topbar (modo, símbolo, métricas live) e Sidebar (Smart Trade, Strategy Lab, Data, Reports, Settings).
- Smart Trade: gráfico de velas `lightweight-charts`, ordens (market/limit/stop/TP/SL/OCO), posições, ordens abertas, KPIs e alertas.
- Strategy Lab: lançamento de Backtest/Grid/WF/Optuna, logs de jobs, runs recentes e relatórios HTML embutidos.
- Data: gestão de pares Bitget, backfill de candles, seleção de DB/símbolo para `config.yaml`.
- Reports: listagem rápida dos relatórios HTML gerados (backtest, grid, WF, ML).
- Settings: editor de configuração (JSON), snapshots/rollback, perfis, alternância de tema (dark/light) e estado da API.
- Hooks utilitários para WebSocket com reconexão, polling e persistência em `localStorage`.

## 🧩 Estrutura do Repositório
- `gui_server.py` — servidor FastAPI, endpoints REST/WS e dispatch de jobs.
- `webapp/` — SPA React moderna (código-fonte e tooling).
- `backtest.py`, `gridsearch.py`, `walkforward.py` — pipeline de backtests.
- `ml_data.py`, `ml_train.py`, `ml_bt.py`, `ml_optuna.py` — pipeline de ML supervisionado.
- `features.py`, `indicators.py`, `strategy.py`, `sizing.py`, `metrics.py`, `broker_futures_paper.py` — lógica de trading e indicadores técnicos.
- `executor_bitget.py` — integração live Bitget (CCXT).
- `db_sqlite.py`, `bitget_backfill.py` — persistência e backfill de candles 5 m.
- `requirements.txt` — dependências Python.

## ⚙️ Pré-Requisitos
- Python 3.10+
- Node.js 18+
- Yarn ou npm (o projeto usa npm por omissão)

## 🚀 Instalação Backend
```bash
python -m venv .venv
source .venv/bin/activate             # Linux/Mac
# .\.venv\Scripts\Activate.ps1       # Windows
pip install -r requirements.txt
```

### Executar Backend
```bash
uvicorn gui_server:app --host 127.0.0.1 --port 8000 --reload
```
A API ficará disponível em `http://127.0.0.1:8000` e servirá a build da SPA (`/`).

## 💻 Instalação Frontend (webapp/)
```bash
cd webapp
npm install
```

### Desenvolvimento com Hot Reload
```bash
npm run dev
```
O Vite sobe em `http://127.0.0.1:5173`. Configure um proxy para as chamadas REST/WS ou inicie o backend simultaneamente.

### Build de Produção
```bash
npm run build
```
Os artefactos são emitidos para `webapp/dist/`, automaticamente servidos pelo FastAPI.

### Qualidade
- `npm run lint` — ESLint + Prettier (TypeScript estrito).
- `npm run typecheck` — `tsc --noEmit` para garantir typings sólidos.

## 📡 Integrações Principais
- `GET /api/live/status` — ticker, posições, saldo, funding, ordens.
- `POST /api/live/order` — envia ordens (market/limit/stop/TP/SL, flags `reduce_only`, `post_only`, `leverage`).
- `POST /api/live/cancel_all`, `POST /api/live/market`, `POST /api/live/set_leverage`.
- `GET /api/candles` — candles OHLCV 5 m (SQLite).
- `GET /api/bitget/pairs`, `POST /api/bitget/backfill` — gestão de dados/pares.
- `GET/POST /api/config/*` — leitura/escrita, snapshots e perfis de `config.yaml`.
- `GET /api/runs/list`, `POST /api/backtest/run`, `POST /api/grid/run`, `POST /api/wf/run`, `POST /api/ml_optuna/run`.
- `GET/POST /api/alerts/*` — alertas personalizados.

## 🧠 Fluxo ML
1. `bitget_backfill.py` preenche o DB SQLite com candles 5 m.
2. `features.py` gera indicadores técnicos e regimes multi-timeframe.
3. `ml_data.py` constrói dataset com labels (retornos após custos).
4. `ml_train.py` treina o MLP (PyTorch) com normalização (`StandardScaler`).
5. `ml_bt.py` avalia o modelo num backtest com gestão de risco.
6. `ml_optuna.py` faz tuning conjunto (hiperparâmetros + risco) e gera relatórios Plotly.

## 📊 Relatórios & Dados
- Cada run cria uma pasta em `data/` com CSVs (`trades.csv`, `equity.csv`) e `report.html`.
- Grid Search também gera `grid_results.csv` (utilizado no dashboard Pareto do Strategy Lab).
- Walk-Forward consolida IS/OOS em `data/walkforward/<run>/` com curva agregada.

## 🔒 Segurança & Boas Práticas
- Nunca exponha API keys no frontend; mantenha-as apenas em `config.yaml` local.
- Utilize `risk_limits` em `config.yaml` para controlar alavancagem, tamanho máximo e perda diária.
- O frontend exibe pré-visualização de risco e bloqueia ordens fora dos limites.

## 🧭 Roadmap Imediato
- Integrar dados live de ordens/posições nas tabelas do Smart Trade.
- Completar widgets do Strategy Lab (logs de jobs e Pareto dinâmico).
- Implementar alertas com som e filtros avançados.

## 🆘 Suporte
Problemas ou sugestões? Abra uma issue descrevendo o cenário, logs relevantes e passos para reproduzir.

Boa sorte e bons trades! 🟢
