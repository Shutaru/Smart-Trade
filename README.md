# 🚀 Smart-Trade - Automated Trading System

Complete algorithmic trading system with **38 strategies**, **dynamic optimization**, **strategy discovery**, and **autonomous agent** with LLM integration.

---

## ✨ **KEY FEATURES**

### 🎯 **Strategy Discovery & Optimization**
- ✅ **38 Built-in Strategies** - Tested and ready to use
- ✅ **Auto-Discovery** - Test all strategies on any symbol automatically
- ✅ **Bayesian Optimization** - Optuna TPE for parameter optimization
- ✅ **Auto-Fetch Data** - Automatically downloads historical data from exchanges
- ✅ **Multi-Symbol Support** - Optimize for multiple symbols simultaneously
- ✅ **Real-time Progress** - Beautiful UI with live progress tracking

### 🤖 **Autonomous Agent**
- ✅ **LLM Integration** - Ollama/Claude for intelligent decision-making
- ✅ **Paper Trading** - Test strategies risk-free
- ✅ **Live Trading** - Deploy optimized strategies to real markets
- ✅ **Portfolio Management** - Multi-strategy portfolio optimization

### 📊 **Data & Analytics**
- ✅ **Exchange Integration** - Bitget & Binance support
- ✅ **Database Caching** - SQLite for fast data access
- ✅ **Indicator Cache** - 44-53% hit rate for performance
- ✅ **Equity Curves** - Real-time performance visualization

---

## 🏗️ **ARCHITECTURE**

```
┌─────────────────────────────────────────────────────────┐
│         FRONTEND (React)                                │
│  - Strategy Discovery UI                                │
│  - Real-time progress tracking                          │
│  - Agent monitoring dashboard                           │
│  - Equity curves & trade analytics                      │
└─────────────────────────────────────────────────────────┘
        ↕️ REST API + WebSocket
┌─────────────────────────────────────────────────────────┐
│        BACKEND (FastAPI)                                │
│  - /api/orchestrator/* - Strategy discovery             │
│  - /api/lab/* - Backtesting & optimization              │
│- /api/agent/* - Autonomous trading agent                │
└─────────────────────────────────────────────────────────┘
            ↕️
┌─────────────────────────────────────────────────────────┐
│  OPTIMIZATION ENGINE                                    │ 
│  - optimizer_dynamic.py - Optuna integration            │
│  - backtest_with_params.py - Dynamic backtest           │
│  - indicators_dynamic.py - 15+ parametrized indicators  │
│  - data_loader.py - Auto-fetch + cache                  │
└─────────────────────────────────────────────────────────┘
           ↕️
┌─────────────────────────────────────────────────────────┐
│       STRATEGIES (38 Total)                             │
│  - Trend Following (12 strategies)                      │
│  - Mean Reversion (10 strategies)                       │
│  - Breakout (8 strategies)                              │
│  - Momentum (8 strategies)                              │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 **QUICK START**

### **Prerequisites**
- Python 3.12+
- Node.js 18+
- Ollama (optional, for LLM features)

### **1. Clone & Setup**
```bash
git clone https://github.com/Shutaru/Smart-Trade.git
cd Smart-Trade

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd webapp
npm install
cd ..
```

### **2. Start Backend**
```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### **3. Start Frontend**
```bash
cd webapp
npm run dev
```

### **4. Access**
- 🎨 **Frontend:** http://localhost:5173
- 🔧 **API Docs:** http://localhost:8000/docs
- 🤖 **Agent:** http://localhost:5173/agent
- 🔍 **Discovery:** http://localhost:5173/orchestrator

---

## 📊 **PROVEN RESULTS**

### **BTC (7 days, 20 trials)**
- **Baseline:** 0.99% profit | 1.80 Sharpe
- **Optimized:** 5.55% profit | 7.77 Sharpe
- **📈 Improvement:** +4.57% (+461% relative!)

### **SOL (7 days, 20 trials - Auto-fetched)**
- **Baseline:** -5.22% profit | -8.99 Sharpe | 28% WR
- **Optimized:** +4.14% profit | +3.91 Sharpe | 62% WR
- **📈 Improvement:** +9.37% (negative → positive!)
- **🔥 Win rate:** +34% (28% → 62%)

### **BTC (90 days, 50 trials)**
- **Baseline:** 10.25% profit | 1.20 Sharpe
- **Optimized:** 26.59% profit | 2.12 Sharpe
- **📈 Improvement:** +16.34% (+159% relative!)

---

## 🎯 **USAGE**

### **Strategy Discovery Workflow**

1. **Select Exchange & Symbols**
- Choose Bitget or Binance
   - Quick-add popular symbols or search
   - Select multiple symbols for batch optimization

2. **Configure Parameters**
   - Historical days (7-1460)
- Optimization trials (10-200)
   - Top N strategies to optimize (3-10)

3. **Run Discovery**
 - System tests all 38 strategies (baseline)
   - Ranks strategies by performance
   - Optimizes top N with Optuna
   - Shows real-time progress

4. **Deploy to Trading**
   - Review best strategies per symbol
   - One-click deploy to paper trading
   - Monitor performance live

---

## 🔧 **CONFIGURATION**

### **Exchange API Keys** (Optional, for live trading)

Create `config.yaml`:
```yaml
exchange: bitget
api_key: YOUR_API_KEY
api_secret: YOUR_API_SECRET
```

### **LLM Configuration** (Optional)

Start Ollama with Llama 3.2:
```bash
ollama run llama3.2:3b
```

---

## 📁 **PROJECT STRUCTURE**

```
Smart-Trade/
├── server/
│   └── main.py    # FastAPI backend
├── webapp/
│   └── src/
│    └── components/
│           ├── Orchestrator/   # Strategy Discovery UI
│           ├── Agent/ # Trading Agent UI
│           └── Lab/   # Backtesting UI
├── optimization/
│   ├── optimizer_dynamic.py    # Optuna optimization
│   ├── backtest_with_params.py # Dynamic backtest
│   ├── parameter_ranges.py     # Auto-detect params
│   └── strategy_param_mapper.py
├── strategies/
│   ├── registry.py     # 38 strategies
│   └── [strategy files]
├── core/
│   ├── indicators_dynamic.py   # Parametrized indicators
│   ├── indicator_cache.py      # Performance cache
│   └── data_loader.py          # Auto-fetch + DB cache
├── orchestrator/
│   └── strategy_discovery.py   # Discovery engine
├── routers/
│   ├── lab.py    # Lab API
│   └── orchestrator.py         # Discovery API
└── backend/agents/
    └── [agent system]
```

---

## 🎓 **SUPPORTED STRATEGIES**

### **Trend Following (12)**
- EMA Cloud, Supertrend, ADX Trend, Ichimoku, HMA Trend, etc.

### **Mean Reversion (10)**
- Bollinger Mean Reversion, RSI Mean Reversion, Bollinger + RSI, etc.

### **Breakout (8)**
- Donchian Breakout, Volume Breakout, Volatility Breakout, etc.

### **Momentum (8)**
- MACD Momentum, Stochastic Momentum, RSI Momentum, etc.

---

## ⚙️ **OPTIMIZATION FEATURES**

- **PROFIT-FIRST v5 Objective** - 95% return weight
- **Intelligent Caching** - 44-53% hit rate
- **Auto-fetch** - Downloads missing data automatically
- **Multi-strategy** - Optimize multiple strategies simultaneously
- **Real-time Progress** - WebSocket updates
- **Database Persistence** - SQLite for results storage

---

## 🤝 **CONTRIBUTING**

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Submit pull request

---

## 📝 **LICENSE**

MIT License - See LICENSE file

---

## 🔗 **LINKS**

- **GitHub:** https://github.com/Shutaru/Smart-Trade
- **Issues:** https://github.com/Shutaru/Smart-Trade/issues

---

## 📞 **SUPPORT**

For questions or issues:
- Open an issue on GitHub
- Check documentation in `/docs`

---

**Built with ❤️ by the Smart-Trade Team**
