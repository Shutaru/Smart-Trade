# ?? Strategy Lab - Status de Implementa��o

## ? **O QUE EST� FUNCIONAL (100%)**

### **1. Frontend Completo**
- ? Strategy Builder (visual UI para construir estrat�gias)
- ? Indicator Selector (RSI, EMA, SMA, Bollinger, etc)
- ? Condition Builder (Entry Long/Short com AND/OR logic)
- ? Objective Function (express�es customizadas: `sharpe - max_dd/10`)
- ? Parameter Space (definir ranges para otimiza��o)
- ? Run Modes: Backtest, Grid Search, Optuna
- ? Real-time Progress (WebSocket updates)
- ? Results Visualization:
  - Metrics Grid (12 m�tricas)
  - **Equity Curve** (Lightweight Charts) ? **N�O APARECE**
  - **Price Action & Trades** (Candlesticks + markers) ? **N�O APARECE**
  - Trades Table (filtros, pagina��o, export CSV)
  - Logs streaming
- ? Download Artifacts (ZIP com CSVs + images)
- ? Compare Runs (multi-run overlay)

### **2. Backend API (100%)**
- ? `/api/lab/exchanges` - Lista exchanges
- ? `/api/lab/symbols` - Lista s�mbolos (CCXT)
- ? `/api/lab/indicators` - Cat�logo de indicadores
- ? `/api/lab/strategy/validate` - Valida configura��o
- ? `/api/lab/backfill` - Baixa dados OHLCV + calcula features
- ? `/api/lab/run/backtest` - Inicia backtest
- ? `/api/lab/run/grid` - Grid search
- ? `/api/lab/run/optuna` - Bayesian optimization
- ? `/api/lab/run/{id}/status` - Status do run
- ? `/api/lab/run/{id}/results` - Resultados (trials)
- ? `/api/lab/run/{id}/candles` - OHLCV para charts
- ? `/api/lab/run/{id}/equity` - Equity curve data
- ? `/api/lab/run/{id}/artifacts/trades` - Trades CSV
- ? `/api/lab/run/{id}/download` - Download ZIP
- ? `/api/lab/compare` - Comparar m�ltiplos runs
- ? `/ws/lab/run/{id}` - WebSocket para updates real-time

### **3. Database (SQLite)**
- ? `strategy_lab.db` - Runs, trials, logs, artifacts
- ? `data/db/BTC_USDT_5m.db` - OHLCV + features (backfilled)
- ? Schema completo com indexes

---

## ? **O QUE N�O EST� IMPLEMENTADO**

### **1. Backtest Engine REAL**
**Ficheiro:** `lab_runner.py` ? `execute_backtest_task()`

**Problema:**
```python
# LINHA 151-156: MOCK DATA HARDCODED
metrics = {
    'total_profit': 45.3,  # ? SEMPRE IGUAL
    'sharpe': 2.1,         # ? SEMPRE IGUAL
    'sortino': 2.8,  # ? SEMPRE IGUAL
    'max_dd': -18.5,       # ? SEMPRE IGUAL
    'win_rate': 58.5,      # ? SEMPRE IGUAL
  'trades': 125       # ? SEMPRE IGUAL
}
```

**O que falta:**
1. ? Carregar dados hist�ricos (OHLCV) do DB
2. ? Calcular indicadores baseados na estrat�gia configurada
3. ? Avaliar condi��es de entrada (Long/Short)
4. ? Simular execu��o de trades
5. ? Calcular m�tricas reais (Sharpe, Sortino, Drawdown)
6. ? Gerar equity curve real
7. ? Gerar trades.csv com timestamps/prices reais

### **2. Grid Search REAL**
**Ficheiro:** `lab_runner.py` ? `execute_grid_search_task()`

**Problema:**
```python
# LINHA 333-341: MOCK DATA COM VARIA��O FAKE
metrics = {
    'total_profit': 45.3 + trial_num * 0.1,  # ? INCREMENTO FAKE
 'sharpe': 2.1 + (trial_num % 10) * 0.05, # ? PADR�O FAKE
    # ...sempre os mesmos valores base
}
```

**O que falta:**
1. ? Para cada combina��o de par�metros ? rodar backtest REAL
2. ? Comparar resultados REAIS

### **3. Optuna REAL**
**Ficheiro:** `lab_runner.py` ? `execute_optuna_task()`

**Problema:**
```python
# LINHA 403-411: MOCK COM SUGEST�ES FAKE
params = {param.name: param.low + (param.high - param.low) * (trial_num / n_trials)}  # ? N�O USA OPTUNA
metrics = {
    'total_profit': 45.3 + trial_num * 0.05,  # ? INCREMENTO LINEAR FAKE
    # ...sempre os mesmos valores base
}
```

**O que falta:**
1. ? `import optuna`
2. ? `study = optuna.create_study(direction='maximize')`
3. ? `study.optimize(objective_function, n_trials=100)`
4. ? Objective function que roda backtest REAL

---

## ?? **PR�XIMOS PASSOS PARA IMPLEMENTA��O REAL**

### **Fase 1: Backtest Engine B�sico (Prioridade ALTA)**

```python
def execute_backtest_task(run_id: str, config: StrategyConfig):
  """Execute REAL backtest"""
    
    # 1. Carregar dados do DB
    symbol = config.data.symbols[0]
    db_path = f"data/db/{symbol.replace('/', '_')}_{config.data.timeframe}.db"
    df = load_ohlcv_from_db(db_path, config.data.since, config.data.until)
    
    # 2. Calcular indicadores
    for condition in config.long.entry_all + config.short.entry_all:
        indicator_func = get_indicator_function(condition.indicator)
df[condition.indicator] = indicator_func(df, **condition.params)
    
    # 3. Simular trades
    trades = []
    position = None
    for i in range(len(df)):
     # Avaliar condi��es de entrada
        if should_enter_long(df.iloc[i], config.long):
            position = open_position('long', df.iloc[i], ...)
      elif should_enter_short(df.iloc[i], config.short):
 position = open_position('short', df.iloc[i], ...)
        
        # Avaliar condi��es de sa�da
        if position and should_exit(df.iloc[i], position):
            trades.append(close_position(position, df.iloc[i]))
            position = None
    
    # 4. Calcular m�tricas REAIS
metrics = calculate_metrics(trades)
    
    # 5. Gerar artifacts REAIS
    save_trades_csv(trades, artifact_dir)
    save_equity_curve(trades, artifact_dir)
    
 return metrics
```

### **Fase 2: Integrar com Grid Search & Optuna**

Depois de ter o backtest REAL, substituir:
- `execute_grid_search_task()` ? chamar `execute_backtest_task()` com params variados
- `execute_optuna_task()` ? usar `optuna.study.optimize()` com objective = `execute_backtest_task()`

---

## ?? **Porque os Charts n�o aparecem**

**TradingChart.tsx** usa Lightweight Charts e precisa de:
1. ? **Dados equity** ? `/api/lab/run/{id}/equity` (funciona)
2. ? **Dados candles** ? `/api/lab/run/{id}/candles` (funciona)
3. ? **Dados trades** ? `/api/lab/run/{id}/artifacts/trades` (funciona)

**Problema:**
- Os dados **existem** mas o componente pode estar a ter erro silencioso no render
- Poss�vel causa: **Lightweight Charts n�o est� a inicializar** (erro de DOM)

**Debug necess�rio:**
```typescript
// Adicionar em TradingChart.tsx
useEffect(() => {
    console.log('[TradingChart] Candles:', candlesData);
  console.log('[TradingChart] Equity:', equityData);
    console.log('[TradingChart] Trades:', tradesData);
    console.log('[TradingChart] Chart ref:', equityChartRef.current);
}, [candlesData, equityData, tradesData]);
```

---

## ?? **RESUMO**

### ? **O que funciona 100%:**
- Interface completa
- API completa
- Database
- WebSocket real-time
- Download artifacts
- Compare runs

### ? **O que est� MOCK:**
- **Backtest engine** (sempre retorna 45.30, 2.10, 58.50...)
- **Grid Search** (fake optimization)
- **Optuna** (fake bayesian)

### ?? **Para ter sistema REAL:**
1. Implementar `execute_backtest_task()` com l�gica real
2. Integrar com Grid/Optuna
3. Debug charts (provavelmente erro de rendering, n�o de dados)

---

## ?? **Ficheiros Chave**

| Ficheiro | Status | Descri��o |
|----------|--------|-----------|
| `lab_runner.py` | ? MOCK | Engine de backtesting |
| `lab_features.py` | ? OK | C�lculo de indicadores |
| `lab_objective.py` | ? OK | Avalia��o de express�es |
| `routers/lab.py` | ? OK | API endpoints |
| `db_sqlite.py` | ? OK | Database operations |
| `TradingChart.tsx` | ?? BUG | Charts n�o renderizam |
| `TradesTable.tsx` | ? OK | Tabela de trades |
| `RunResults.tsx` | ? OK | P�gina de resultados |

---

**�ltima atualiza��o:** 28/10/2025 17:50
**Status geral:** ?? **Frontend 100% + Backend API 100% + Backtest Engine 0%**
