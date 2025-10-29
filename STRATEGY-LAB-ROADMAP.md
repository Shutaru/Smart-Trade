# ?? Strategy Lab - Roadmap & Implementation Guide

## ?? **Current State (O que já está implementado)**

### ? **Backend - 100% Funcional**
- ? `/api/lab/strategy/validate` - Validação de estratégias
- ? `/api/lab/run/backtest` - Backtest execution (REAL engine)
- ? `/api/lab/run/grid` - Grid search optimization
- ? `/api/lab/run/optuna` - Bayesian optimization
- ? `/api/lab/run/{run_id}/status` - Progress tracking
- ? `/api/lab/run/{run_id}/results` - Trial results
- ? `/api/lab/run/{run_id}/candles` - OHLCV data
- ? `/api/lab/run/{run_id}/equity` - Equity curve
- ? `/api/lab/run/{run_id}/artifacts/trades` - Trades list
- ? `/api/lab/runs` - List all runs
- ? `/api/lab/run/{run_id}/download` - Download artifacts (ZIP)
- ? `/api/lab/compare` - Compare multiple runs
- ? WebSocket `/ws/lab/run/{run_id}` - Real-time progress

### ? **Backend - Production Backtest Engine**
- ? `lab_backtest_adapter.py` - Conecta Strategy Lab ao backtest.py
- ? `lab_runner.py` - Async execution com ThreadPoolExecutor
- ? `lab_objective.py` - Safe objective evaluator (numexpr)
- ? `lab_features.py` - Technical indicators (RSI, EMA, MACD, etc)
- ? `broker_futures_paper.py` - Paper trading broker
- ? `db_sqlite.py` - Database for runs, trials, logs, artifacts

### ? **Frontend - Strategy Builder**
- ? `StrategyLab.tsx` - Main component com tabs
- ? `DataSelector.tsx` - Exchange, symbols, timeframe selection
- ? `StrategyBuilder.tsx` - Long/Short conditions (entry_all, entry_any)
- ? `ExitRulesEditor.tsx` - TP/SL rules
- ? `RiskPanel.tsx` - Portfolio size, leverage, position sizing
- ? `ObjectiveEditor.tsx` - Custom objective functions
- ? `ParamRangesEditor.tsx` - Parameter ranges for optimization
- ? Run modes: Backtest, Grid Search, Optuna

### ? **Frontend - Results Dashboard**
- ? `ResultsDashboard.tsx` - KPIs + charts + trades table
- ? `TradingChart.tsx` - Equity curve + Candle chart with markers
- ? `MetricsGrid.tsx` - Sharpe, Sortino, Win Rate, etc
- ? `TradesTable.tsx` - Trade history with filters
- ? Real-time progress via WebSocket

---

## ?? **O QUE FALTA IMPLEMENTAR (Próximos Prompts)**

### **Prompt #1: Melhorar Grid Search & Optuna (Backend)**

**Objetivo:** Implementar Grid Search e Optuna **REAIS** (atualmente são mocks)

#### **Backend Tasks:**
1. **Grid Search Real:**
   - Gerar todas as combinações de `param_space`
   - Executar backtest para cada combinação
   - Salvar trials em `db_sqlite`
   - Broadcast progress via WebSocket

2. **Optuna Real:**
   - Integrar `optuna.create_study()`
   - Bayesian optimization com TPE sampler
   - Sugerir parâmetros inteligentemente
   - Early stopping se não melhorar

#### **Files to Modify:**
```python
# lab_runner.py
def execute_grid_search_task(run_id, config):
    # TODO: Replace mock with real grid search
    # Generate param combinations
    # For each combination:
 #   - Update strategy config with params
    #   - Run backtest using lab_backtest_adapter
    #   - Calculate objective score
#   - Save trial to database
    pass

def execute_optuna_task(run_id, config, n_trials):
    # TODO: Replace mock with real Optuna
    import optuna
    
    def objective_function(trial):
        # Suggest params from param_space
   params = {p.name: trial.suggest_float(p.name, p.low, p.high) for p in config.param_space}
      # Run backtest
        metrics = run_strategy_lab_backtest(config, artifact_dir)
        # Return objective score
   return evaluate_objective(metrics, config.objective.expression)
    
    study = optuna.create_study(direction='maximize')
    study.optimize(objective_function, n_trials=n_trials, callbacks=[ws_callback])
    pass
```

#### **Expected Output:**
- Grid Search: Test 1000+ combinations em ~10-30 minutos
- Optuna: Converge para melhor resultado em 100 trials

---

### **Prompt #2: Blackbox Mode (Advanced Optimization)**

**Objetivo:** Adicionar modo "Blackbox" - optimization sem visualizar estratégia

#### **Backend Tasks:**
1. Criar endpoint `/api/lab/run/blackbox`
2. Aceitar apenas:
   - Data specification
   - Objective function
   - Param space (large)
3. Usar algoritmo avançado (CMA-ES, NSGA-II, ou Optuna com pruning)

#### **Frontend Tasks:**
1. Novo tab "Blackbox" no StrategyLab
2. Configuração minimalista:
   - Data range
   - Optimization budget (trials)
   - Objective expression
3. Results page com Pareto frontier (multi-objective)

#### **Files to Create:**
```python
# lab_optimizer_blackbox.py
def run_blackbox_optimization(data_spec, objective, param_space, n_trials):
    """
    Advanced optimization without predefined strategy
    Uses CMA-ES or NSGA-II for parameter search
    """
    pass
```

---

### **Prompt #3: Export & Import Strategies**

**Objetivo:** Salvar e carregar estratégias completas

#### **Backend Tasks:**
1. Endpoint `/api/lab/strategy/export` - Export strategy as JSON/YAML
2. Endpoint `/api/lab/strategy/import` - Import strategy from file
3. Endpoint `/api/lab/strategy/templates` - List built-in templates

#### **Frontend Tasks:**
1. Botão "Export Strategy" ? Download JSON
2. Botão "Import Strategy" ? Upload JSON e preencher form
3. Gallery de templates prontos:
   - RSI Oversold/Overbought
   - EMA Crossover
   - Bollinger Bands Mean Reversion
   - Breakout Strategy

#### **Files to Create:**
```python
# routers/lab.py
@router.post("/strategy/export")
async def export_strategy(config: StrategyConfig):
    return {"strategy_json": config.model_dump_json()}

@router.post("/strategy/import")
async def import_strategy(file: UploadFile):
    content = await file.read()
    config = StrategyConfig.model_validate_json(content)
    return {"config": config.model_dump()}
```

---

### **Prompt #4: Advanced Charts & Analytics**

**Objetivo:** Melhorar visualizações e adicionar análises avançadas

#### **Frontend Tasks:**
1. **Heatmap de parâmetros** (Grid Search results)
2. **Pareto Frontier** (Multi-objective optimization)
3. **Parameter Importance** (Feature importance plot)
4. **Rolling Sharpe** (Sharpe over time)
5. **Drawdown Calendar** (Heatmap de drawdowns mensais)
6. **Trade Distribution** (Histogram de PnL)

#### **Components to Create:**
```tsx
// HeatmapChart.tsx - Parameter heatmap
// ParetoChart.tsx - Multi-objective Pareto frontier
// RollingSharpeChart.tsx - Rolling window Sharpe ratio
// DrawdownCalendar.tsx - Calendar heatmap
```

---

### **Prompt #5: Walk-Forward Analysis**

**Objetivo:** Implementar Walk-Forward testing para validação robusta

#### **Backend Tasks:**
1. Dividir dados em períodos (In-Sample / Out-of-Sample)
2. Otimizar em IS, testar em OS
3. Rolling window (e.g., 6 meses IS, 2 meses OS)
4. Calcular stability score

#### **Files to Create:**
```python
# lab_walk_forward.py
def run_walk_forward(config, is_periods, os_periods):
    """
    Run walk-forward analysis:
    1. Split data into IS/OS periods
    2. Optimize on IS
    3. Test on OS
    4. Repeat
    """
    pass
```

---

### **Prompt #6: Live Trading Integration (Future)**

**Objetivo:** Deploy estratégias otimizadas para live trading

#### **Tasks:**
1. Endpoint `/api/lab/deploy` - Deploy strategy to live bot
2. Integração com `live_bot.py` existente
3. Dashboard de monitoramento em tempo real
4. Kill switch automático se drawdown > threshold

---

## ?? **Prompt Templates**

### **Template para Prompt #1 (Grid Search Real):**
```
Implementar Grid Search REAL no lab_runner.py:

1. Modificar execute_grid_search_task():
   - Gerar todas as combinações de param_space usando itertools.product
   - Para cada combinação:
     * Atualizar config.risk com os parâmetros
     * Executar run_strategy_lab_backtest(config, artifact_dir)
     * Calcular objective score usando evaluate_objective()
   * Inserir trial em db_sqlite com db_sqlite.insert_trial()
     * Broadcast progress via log_run() para WebSocket
   
2. Limitar a 5000 combinações máximo (para evitar overload)

3. Ordenar results por score e salvar best trial

4. Testar com estratégia simples (2-3 parâmetros)
```

### **Template para Prompt #2 (Export/Import):**
```
Adicionar funcionalidade de Export/Import de estratégias:

Backend:
1. POST /api/lab/strategy/export - Return strategy JSON
2. POST /api/lab/strategy/import - Accept JSON file

Frontend:
1. Botão "Export" em StrategyLab ? Download strategy.json
2. Botão "Import" ? Upload e preencher form automaticamente
3. Gallery de templates (3-4 estratégias prontas)
```

---

## ?? **Quick Start Guide (Para próximo prompt)**

**Para implementar Grid Search REAL:**
1. Modificar `lab_runner.py::execute_grid_search_task()`
2. Usar `itertools.product()` para gerar combinações
3. Executar `run_strategy_lab_backtest()` para cada trial
4. Salvar em database e broadcast progress
5. Testar com 2-3 parâmetros (e.g., SL multiplier, TP multiplier)

---

## ? **Checklist de Implementação**

### **Fase 1: Optimization (Próximos 2-3 prompts)**
- [ ] Grid Search REAL
- [ ] Optuna REAL com TPE sampler
- [ ] Blackbox mode
- [ ] Walk-Forward Analysis

### **Fase 2: UX/UI (Prompts 4-5)**
- [ ] Export/Import strategies
- [ ] Strategy templates gallery
- [ ] Advanced charts (Heatmap, Pareto, Rolling Sharpe)
- [ ] Drawdown calendar

### **Fase 3: Production (Future)**
- [ ] Live trading deployment
- [ ] Real-time monitoring dashboard
- [ ] Alerting system
- [ ] Portfolio of strategies

---

## ?? **Recursos Úteis**

### **Optuna Documentation:**
- https://optuna.readthedocs.io/
- TPE Sampler: `optuna.samplers.TPESampler()`
- Pruning: `optuna.pruners.MedianPruner()`

### **Grid Search:**
- `itertools.product()` para combinações
- Paralelização com `ThreadPoolExecutor`
- Progress tracking via `tqdm` ou custom logger

### **Walk-Forward:**
- Anchored vs Rolling window
- IS/OS ratio (typically 3:1 or 6:2)
- Stability score: correlation(IS_score, OS_score)

---

## ?? **Próximo Prompt Sugerido:**

```
"Implementar Grid Search REAL e Optuna REAL no lab_runner.py. 
Grid Search deve testar todas as combinações de param_space e executar 
backtests reais. Optuna deve usar TPE sampler e convergir para o melhor 
resultado. Adicionar progress tracking via WebSocket."
```

---

**Tudo pronto para os próximos passos! ??**
