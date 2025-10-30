# Plataforma de Trading Algorítmico para Futuros (Bitget)

Bem-vindo a uma plataforma de trading de alta performance, local-first e API-driven, desenhada para a automação e análise de estratégias de trading de futuros, com foco inicial na exchange **Bitget**.

Inspirada em terminais profissionais como o 3Commas, esta aplicação combina um backend robusto em Python para análise e execução, com um frontend moderno e reativo em React, criando uma experiência de "Smart Terminal" completa.

---

## ✨ Funcionalidades Principais

### 🚀 Frontend: O Smart Terminal

A interface de utilizador foi totalmente reconstruída em **React + TypeScript** para oferecer uma experiência de produto polida, rápida e intuitiva.

-   **🖥️ Smart Trade:** Um painel de trading completo com gráficos de velas em tempo real (`lightweight-charts`), atualização via WebSocket, painel de ordens avançado (Market, Limit, Stop, Bracket Orders), e gestão de posições e ordens abertas.
-   **📊 Trading Chart Advanced:** Gráfico de trading profissional com:
    - **Timeframe Selector:** Alterne entre 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d
    - **Indicators Overlay:** EMA20, EMA50, SMA200, Bollinger Bands
    - **Settings Panel:** Ative/desative indicadores em tempo real
    - **Auto-refresh:** Atualização automática a cada 5s
-   **🤖 Agent Runner:** Sistema de trading autónomo com LLM:
    - **Autonomous Decision Making:** LLM analisa mercado + notícias para decisões inteligentes
    - **Multi-Strategy Portfolio:** Gere múltiplas estratégias simultaneamente (Conservative 45%, Balanced 40%, Aggressive 15%)
    - **Real-time Monitoring:** Equity curve, posições abertas, risk metrics
    - **Event Log:** Histórico completo de ações e decisões do agente
- **🔬 Strategy Lab:** Lance tarefas complexas de análise diretamente da UI. Inicie Backtests, Grid Searches, Walk-Forward Analysis e Otimizações de Hiperparâmetros com **ML Optuna**.
-   **💾 Gestão de Dados:** Um hub para gerir os dados de mercado. Liste todos os pares de futuros disponíveis na Bitget e faça o *backfill* de dados históricos com um único clique.
-   **📊 Relatórios:** Visualize os relatórios HTML gerados pelas suas análises (equity, drawdown, heatmaps, etc.) diretamente na aplicação.
-   **⚙️ Configuração Centralizada:**
    -   **Editor Visual:** Edite o seu ficheiro `config.yaml` num editor JSON seguro.
    -   **Snapshots:** Crie e reverta para versões anteriores da sua configuração.
    -   **Perfis:** Guarde, exporte, importe e aplique diferentes perfis de estratégia.

### 🐍 Backend: O Motor de Análise e Execução

O coração da plataforma é um servidor **FastAPI** que expõe uma API REST + WebSocket para todas as operações.

-**🤖 Strategy Discovery Engine:** Sistema autónomo de descoberta de estratégias:
    - **26 Indicadores Técnicos:** RSI, MACD, EMA, SMA, ADX, ATR, Bollinger, SuperTrend, Donchian, Stochastic, CCI, MFI, OBV, VWAP
    - **Parallel Backtesting:** Testa 10+ estratégias em paralelo usando asyncio
    - **Advanced Ranking Formula:** Score composto que minimiza drawdown e maximiza retornos estáveis
    - **Automatic Strategy Generation:** Combinações inteligentes de indicadores (Trend + Momentum + Volatility)

-   **📊 Multi-Strategy Portfolio Manager:**
    - **Portfolio Allocation:** Gestão de capital entre 3 estratégias (Conservative, Balanced, Aggressive)
    - **Risk-Adjusted Weights:** Alocação baseada em Sharpe Ratio, Calmar Ratio, e Sortino Ratio
    - **Dynamic Rebalancing:** Rebalanceamento automático quando drift > threshold
    - **Performance Tracking:** Monitorização de PnL, win rate, drawdown por estratégia
    - **Strategy Categorization:** Classificação automática por perfil de risco

-   **🧠 ML Suite (GPU + Optuna):** Utilize o poder do `ml_optuna.py` para otimizar os seus modelos de Machine Learning, aproveitando todas as GPUs disponíveis para maximizar a performance (e.g., Sharpe Ratio).
-   **🧭 Modos Paper vs. Live:** Alterne facilmente entre trading simulado (paper) e real (live). O modo é persistido no `config.yaml` para segurança.
-   **🔧 Estratégia e Tuning:** O sistema suporta uma vasta gama de indicadores (Stochastic, CCI, MACD, Supertrend) e tipos de Stop Loss/Take Profit (`atr_trailing`, `chandelier`, `breakeven_then_trail`).
-   **📈 Geração de Relatórios:** Cada backtest ou otimização gera um `report.html` detalhado com curvas de equity, drawdowns, KPIs, e visualizações gráficas.
-   **⏱️ Monitorização de Progresso:** Todos os jobs de longa duração (backtests, ML) reportam o seu progresso, permitindo que a UI exiba barras de progresso com **ETA** (Tempo Estimado de Conclusão).

---

## 🏗️ Arquitetura do Sistema Agentic

```
┌─────────────────────────────────────────────────────────┐
│          🤖 AGENTIC TRADING SYSTEM (v0.2.0)            │
├─────────────────────────────────────────────────────────┤
│        │
│  1️⃣ STRATEGY DISCOVERY ENGINE           │
│     ├─ 26 Technical Indicators                 │
│     ├─ Parallel Backtest Runner (asyncio)         │
│     ├─ Advanced Ranking Formula              │
│     └─ Top 3 Strategy Selection     │
│        │
│  2️⃣ MULTI-STRATEGY PORTFOLIO MANAGER         │
│     ├─ Conservative (45%): High Sharpe, Low DD          │
│     ├─ Balanced (40%): Optimal Risk/Reward              │
│     ├─ Aggressive (15%): High Return, High Vol  │
│     └─ Dynamic Rebalancing System           │
│       │
│  3️⃣ LIVE DECISION ENGINE (Coming Soon)     │
│     ├─ LLM Analyzer (Claude/GPT-4)       │
│     ├─ RSS News Feed Integration       │
│     ├─ Context-Aware Decision Making         │
│     └─ Long + Short Execution               │
│ │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

-   **Frontend:** React, Vite, TypeScript, TailwindCSS, shadcn/ui, TanStack Query, lightweight-charts, Framer Motion.
-   **Backend:** Python 3, FastAPI, Uvicorn.
-   **Análise & Trading:** CCXT, Pandas, NumPy, Scikit-learn, PyTorch, Optuna.
-   **Base de Dados:** SQLite para dados de mercado.
-   **Strategy Discovery:** Asyncio, YAML, Custom Ranking Algorithm
-   **Portfolio Management:** Dataclasses, Type Hints, Performance Tracking

---

## 🚀 Guia de Iniciação Rápida

Siga estes passos para ter a plataforma a correr localmente.

### Pré-requisitos
-   Python 3.8+
-   Node.js 18+ e npm

### ⚡ Método Rápido: Scripts 1-Click (Windows)

#### Modo Desenvolvimento (Hot Reload)
```powershell
# Inicia backend (FastAPI) e frontend (Vite) com hot-reload
.\start-dev.ps1
```

**O que faz:**
- ✅ Verifica dependências (Python venv, node_modules)
- ✅ Instala dependências se necessário
- ✅ Inicia backend em `http://127.0.0.1:8000` (nova janela)
- ✅ Inicia frontend em `http://localhost:5173` (nova janela)
- ✅ Hot-reload ativo em ambos

#### Modo Produção (Build Otimizado)
```powershell
# Build do frontend + serve via FastAPI
.\start-prod.ps1
```

**O que faz:**
- ✅ Executa `npm ci` (clean install)
- ✅ Build otimizado do frontend (`npm run build`)
- ✅ Serve frontend + backend em `http://0.0.0.0:8000`
- ✅ Pronto para deploy (single server)

---

## 🧪 Testar Novos Módulos

### Test Strategy Discovery Engine
```powershell
python test_discovery.py
```
**Output esperado:**
- ✅ 21 indicadores técnicos carregados
- ✅ 20 templates de estratégias gerados
- ✅ Ranking de 4 estratégias por score composto

### Test Multi-Strategy Portfolio
```powershell
python test_portfolio.py
```
**Output esperado:**
- ✅ Seleção e categorização de 3 estratégias
- ✅ Alocação: Conservative 45%, Balanced 40%, Aggressive 15%
- ✅ Simulação de 9 trades com PnL tracking
- ✅ Performance report detalhado

---

## 📋 Método Manual: Passo a Passo

#### 1. Configuração do Backend
```bash
# Clone o repositório
git clone <URL_DO_SEU_REPOSITORIO>
cd <NOME_DA_PASTA>

# Crie virtual environment (recomendado)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instale as dependências Python
pip install -r requirements.txt

# Crie e configure o seu ficheiro de configuração
cp config.example.yaml config.yaml
# Edite config.yaml e adicione as suas chaves de API da Bitget

# (Opcional mas recomendado) Faça o backfill inicial de dados para um par
# Execute o script bitget_backfill.py ou use a UI mais tarde

# Inicie o servidor FastAPI
uvicorn gui_server:app --reload
```
O backend estará agora a correr em `http://127.0.0.1:8000`.

#### 2. Configuração do Frontend
Num novo terminal:
```bash
# Navegue para a pasta da aplicação web
cd webapp

# Instale as dependências Node.js
npm install

# Inicie o servidor de desenvolvimento Vite
npm run dev
```
O frontend estará agora acessível em `http://localhost:5173`.

A interface irá ligar-se automaticamente ao backend através do proxy configurado no Vite.

---

## 🔧 Scripts Disponíveis

| Script | Descrição | Uso |
|--------|-----------|-----|
| `start-dev.ps1` | Dev mode com hot-reload | Desenvolvimento diário |
| `start-prod.ps1` | Build + produção | Deploy local/servidor |
| `test_discovery.py` | Teste Strategy Discovery | Validar ranking engine |
| `test_portfolio.py` | Teste Portfolio Manager | Validar multi-strategy |
| `webapp/npm run dev` | Só frontend | Debug frontend |
| `uvicorn gui_server:app --reload` | Só backend | Debug backend |

---

## 📚 Estrutura do Projeto

```
Smart-Trade/
├── backend/
│   └── agents/
│       ├── discovery/          # 🆕 Strategy Discovery Engine
│       │   ├── strategy_catalog.py    # 26 indicadores técnicos
│     │   ├── ranker.py   # Advanced scoring formula
│       │   └── discovery_engine.py    # Parallel backtest runner
│     ├── portfolio/  # 🆕 Multi-Strategy Portfolio
│       │   ├── strategy_selector.py   # Strategy categorization
│   │   ├── portfolio_manager.py   # Portfolio allocation
│       │   └── rebalancer.py          # Dynamic rebalancing
│       ├── policies/       # Trading policies (LLM, rule-based)
│       ├── tools/        # Market data, execution tools
│       └── service.py          # Agent orchestration
├── webapp/
│   └── src/
│       └── components/
│  └── Agent/  # 🆕 Agent Runner UI
│               ├── Agent.tsx               # Main dashboard
│               ├── EquityChart.tsx  # Equity curve
│               └── TradingChartAdvanced.tsx # Advanced chart
├── test_discovery.py           # 🆕 Test strategy discovery
├── test_portfolio.py    # 🆕 Test portfolio manager
├── gui_server.py            # FastAPI server
└── config.yaml            # Main configuration
```

---

## 🎯 Roadmap

### ✅ Concluído (v0.2.0)
- [x] Strategy Discovery Engine (26 indicadores)
- [x] Multi-Strategy Portfolio Manager
- [x] Advanced Ranking Formula
- [x] Trading Chart with Timeframes & Indicators
- [x] Agent Runner Dashboard

### 🚧 Em Progresso (v0.3.0)
- [ ] Strategy Optimizer (Optuna Bayesian Optimization)
- [ ] LLM Decision Engine (Claude/GPT-4 integration)
- [ ] RSS News Feed Integration
- [ ] Context-Aware Trade Execution

### 📅 Planeado (v0.4.0)
- [ ] Neural Network Strategy Trainer
- [ ] Multi-Exchange Support (Binance, Bybit)
- [ ] Backtesting com Dados de Order Book
- [ ] Sentiment Analysis Integration

---

## 📄 Licença

Este projeto está sob a licença MIT. Consulte o ficheiro LICENSE para mais detalhes.

---

## 🤝 Contribuir

Contribuições são bem-vindas! Abra issues e pull requests.

---

**Feito com ❤️ para traders algorítmicos**
