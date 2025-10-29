# Plataforma de Trading Algorítmico para Futuros (Bitget)

Bem-vindo a uma plataforma de trading de alta performance, local-first e API-driven, desenhada para a automação e análise de estratégias de trading de futuros, com foco inicial na exchange **Bitget**.

Inspirada em terminais profissionais como o 3Commas, esta aplicação combina um backend robusto em Python para análise e execução, com um frontend moderno e reativo em React, criando uma experiência de "Smart Terminal" completa.

---

## ✨ Funcionalidades Principais

### 🚀 Frontend: O Smart Terminal

A interface de utilizador foi totalmente reconstruída em **React + TypeScript** para oferecer uma experiência de produto polida, rápida e intuitiva.

-   **🖥️ Smart Trade:** Um painel de trading completo com gráficos de velas em tempo real (`lightweight-charts`), atualização via WebSocket, painel de ordens avançado (Market, Limit, Stop, Bracket Orders), e gestão de posições e ordens abertas.
-   **🤖 Gestão de Bots:** Crie, configure e gira bots de trading automatizados. Monitorize o seu estado (Running, Paused, Stopped), modo (Paper/Live) e performance (PnL) a partir de um dashboard centralizado.
-   **🔬 Strategy Lab:** Lance tarefas complexas de análise diretamente da UI. Inicie Backtests, Grid Searches, Walk-Forward Analysis e Otimizações de Hiperparâmetros com **ML Optuna**.
-   **💾 Gestão de Dados:** Um hub para gerir os dados de mercado. Liste todos os pares de futuros disponíveis na Bitget e faça o *backfill* de dados históricos com um único clique.
-   **📊 Relatórios:** Visualize os relatórios HTML gerados pelas suas análises (equity, drawdown, heatmaps, etc.) diretamente na aplicação.
-   **⚙️ Configuração Centralizada:**
    -   **Editor Visual:** Edite o seu ficheiro `config.yaml` num editor JSON seguro.
    -   **Snapshots:** Crie e reverta para versões anteriores da sua configuração.
    -   **Perfis:** Guarde, exporte, importe e aplique diferentes perfis de estratégia.

### 🐍 Backend: O Motor de Análise e Execução

O coração da plataforma é um servidor **FastAPI** que expõe uma API REST + WebSocket para todas as operações.

-   **🧠 ML Suite (GPU + Optuna):** Utilize o poder do `ml_optuna.py` para otimizar os seus modelos de Machine Learning, aproveitando todas as GPUs disponíveis para maximizar a performance (e.g., Sharpe Ratio).
-   **🧭 Modos Paper vs. Live:** Alterne facilmente entre trading simulado (paper) e real (live). O modo é persistido no `config.yaml` para segurança.
-   **🔧 Estratégia e Tuning:** O sistema suporta uma vasta gama de indicadores (Stochastic, CCI, MACD, Supertrend) e tipos de Stop Loss/Take Profit (`atr_trailing`, `chandelier`, `breakeven_then_trail`).
-   **📈 Geração de Relatórios:** Cada backtest ou otimização gera um `report.html` detalhado com curvas de equity, drawdowns, KPIs, e visualizações gráficas.
-   **⏱️ Monitorização de Progresso:** Todos os jobs de longa duração (backtests, ML) reportam o seu progresso, permitindo que a UI exiba barras de progresso com **ETA** (Tempo Estimado de Conclusão).

---

## 🛠️ Tech Stack

-   **Frontend:** React, Vite, TypeScript, TailwindCSS, shadcn/ui, TanStack Query, lightweight-charts, Framer Motion.
-   **Backend:** Python 3, FastAPI, Uvicorn.
-   **Análise & Trading:** CCXT, Pandas, NumPy, Scikit-learn, PyTorch, Optuna.
-   **Base de Dados:** SQLite para dados de mercado.

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

### 📋 Método Manual: Passo a Passo

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
| `webapp/npm run dev` | Só frontend | Debug frontend |
| `uvicorn gui_server:app --reload` | Só backend | Debug backend |

---
