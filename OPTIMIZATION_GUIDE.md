# Strategy Optimization System

Complete system for discovering, optimizing, and deploying trading strategies.

---

## ?? **Workflow Overview**

```
1. DISCOVERY (38 strategies × 3 timeframes)
   ?
2. RANKING (Return-first scoring)
   ?
3. OPTIMIZATION (TOP 5 strategies with Optuna)
 ?
4. VALIDATION (Walk-forward, out-of-sample)
 ?
5. DEPLOYMENT (Live trading)
```

---

## ?? **Phase 1: Strategy Discovery**

### **Run Discovery on All Timeframes**

```bash
python run_discovery_comparison.py
```

**What it does:**
- Tests 38 professional strategies on 5min, 1h, and 4h timeframes
- Runs 114 backtests (38 × 3) sequentially
- Uses Return-First scoring (60% weight on absolute returns)
- Saves results to `data/discovery_comparison/`

**Duration:** ~90-110 minutes

**Output:**
- `results_5m_<timestamp>.txt`
- `results_1h_<timestamp>.txt`
- `results_4h_<timestamp>.txt`

---

## ?? **Phase 2: Select Best Timeframe & Strategies**

After discovery completes, review results:

```bash
# View summary (automatically printed at end of discovery)
```

**Metrics to consider:**
- Number of profitable strategies
- Best Sharpe ratios
- Lowest drawdowns
- Trade frequency (2-10 trades/day ideal)

**Example decision:**
```
5min: 5/38 profitable, Best Sharpe: 4.36
1h:   8/38 profitable, Best Sharpe: 3.89
4h:   3/38 profitable, Best Sharpe: 2.45

? Choose 1h (most profitable, good Sharpe, manageable trade frequency)
```

---

## ?? **Phase 3: Optimize TOP 5 Strategies**

### **Run Optimization**

```bash
python optimize_top_strategies.py --timeframe 1h --trials 50 --top-n 5
```

**Arguments:**
- `--timeframe`: Which timeframe to optimize (5m, 1h, 4h)
- `--trials`: Number of optimization trials per strategy (default: 30)
- `--top-n`: Number of top strategies to optimize (default: 5)
- `--objective`: Objective function (sharpe, return, calmar, custom)

**What it does:**
- Loads TOP 5 strategies from discovery results
- Runs Bayesian optimization (Optuna TPE sampler) on each
- Tests parameter combinations:
  - RSI periods (7-28)
  - ADX thresholds (15-35)
  - ATR multipliers (1.0-3.5)
  - EMA periods (8-100)
  - Entry/exit conditions
- Saves best parameters for each strategy

**Duration:** ~2-3 hours (50 trials × 5 strategies)

**Output:**
- `data/optimization/<study_name>/optimization_results.json`
- `data/optimization/top5_<timeframe>_<timestamp>/optimization_summary.json`

---

## ?? **Phase 4: Generate Comparison Report**

### **Create HTML Report**

```bash
python optimization_report.py
```

Or automatically generated after optimization completes.

**Report includes:**
- Interactive Plotly charts
- Side-by-side strategy comparison
- Best parameters for each strategy
- Performance metrics (Sharpe, Return, DD, Win Rate)
- Ranked leaderboard

**Output:**
- `data/optimization/report_<timestamp>.html`
- Open in browser for interactive visualization

---

## ?? **Phase 5: Validation (Walk-Forward)**

### **Walk-Forward Analysis**

```bash
python walkforward.py --strategy obv_range_fade --is 180 --os 60 --folds 6
```

**Arguments:**
- `--strategy`: Strategy name (from TOP 5)
- `--is`: In-sample days (training period)
- `--os`: Out-of-sample days (test period)
- `--folds`: Number of folds (walk-forward windows)

**What it does:**
- Splits data into training/test windows
- Optimizes on in-sample, validates on out-of-sample
- Detects overfitting
- Calculates degradation factor (OS performance / IS performance)

**Good indicators:**
- Degradation factor > 0.7 (OS Sharpe ? 70% of IS Sharpe)
- Consistent profitability across folds
- Similar trade frequency in IS vs OS

---

## ??? **Phase 6: Deploy to Live Trading**

### **Apply Best Parameters to Config**

After optimization, apply best parameters:

```python
# In optimize_top_strategies.py, results are saved to:
# data/optimization/<strategy_name>/optimization_results.json

# Manually update config.yaml with best parameters, or use:
python apply_optimization_results.py --strategy obv_range_fade
```

### **Start Live Trading**

```bash
# Paper trading first (ALWAYS!)
python agent_runner.py --config configs/agent_paper.yaml

# After 1-2 weeks of successful paper trading:
python agent_runner.py --config configs/agent_live.yaml
```

---

## ?? **File Structure**

```
Smart-Trade/
??? run_discovery_comparison.py      # Phase 1: Discovery
??? optimize_top_strategies.py       # Phase 3: Optimization
??? optimization_report.py       # Phase 4: Reports
??? strategy_optimizer.py    # Optuna optimization engine
??? walkforward.py           # Phase 5: Validation
?
??? backend/agents/discovery/
?   ??? discovery_engine.py    # Discovery engine (modified for timeframes)
?   ??? strategy_catalog.py    # 38 strategy definitions
?   ??? entry_logic_builder.py       # Entry logic generation
?   ??? ranker.py         # Return-first scoring (modified)
?
??? data/
    ??? discovery_comparison/        # Discovery results
    ??? optimization/          # Optimization results
    ?   ??? top5_5m_<ts>/
    ?   ??? top5_1h_<ts>/
    ?   ??? report_<ts>.html
    ??? walkforward/            # Walk-forward results
```

---

## ?? **Optimization Details**

### **Parameter Ranges (Default)**

| Indicator | Parameter | Range | Type |
|-----------|-----------|-------|------|
| RSI | period | 7-28 | int |
| RSI | oversold | 15-35 | int |
| RSI | overbought | 65-85 | int |
| EMA | fast_period | 8-25 | int |
| EMA | slow_period | 30-100 | int |
| ADX | period | 10-25 | int |
| ADX | threshold | 15-35 | int |
| ATR | period | 10-20 | int |
| ATR | sl_multiplier | 1.0-3.5 | float |
| ATR | tp_multiplier | 1.5-4.0 | float |
| Bollinger | period | 15-30 | int |
| Bollinger | std_dev | 1.5-3.0 | float |

### **Objective Functions**

| Objective | Formula | Use Case |
|-----------|---------|----------|
| `sharpe` | Sharpe Ratio (ann.) | Risk-adjusted returns |
| `return` | Total Return % | Maximize profit |
| `calmar` | Return / Max DD | Return per unit risk |
| `custom` | Sharpe - (DD / 20) | Balanced (reward high Sharpe, penalize DD) |

---

## ?? **Best Practices**

### **? DO:**
- Always run discovery on 3 timeframes
- Optimize TOP 5 only (avoid overfitting to noise)
- Use 30-50 trials per strategy (Bayesian converges fast)
- Validate with walk-forward (detect overfitting)
- Paper trade for 1-2 weeks before live
- Monitor degradation factor (>0.7 is good)

### **? DON'T:**
- Optimize on entire dataset (use train/test split)
- Cherry-pick best backtest (use walk-forward)
- Over-optimize (>100 trials can overfit)
- Skip paper trading
- Deploy without monitoring

---

## ?? **Troubleshooting**

### **Discovery fails with "Insufficient backfill"**
```bash
# Backfill more data
python bitget_backfill.py --symbol BTC/USDT:USDT --days 1460 --timeframe 5m
python bitget_backfill.py --symbol BTC/USDT:USDT --days 1460 --timeframe 1h
python bitget_backfill.py --symbol BTC/USDT:USDT --days 1460 --timeframe 4h
```

### **Optimization takes too long**
- Reduce `--trials` to 20-30
- Use `--top-n 3` instead of 5
- Optimize only best timeframe

### **All strategies unprofitable**
- Check market regime (bull/bear/sideways)
- Try different timeframe (crypto volatility varies)
- Adjust parameter ranges (may need wider search)

---

## ?? **Expected Results**

Based on 4 years BTC/USDT data (2021-2025):

| Timeframe | Profitable | Best Sharpe | Avg Return | Best Strategy |
|-----------|------------|-------------|------------|---------------|
| 5min | 5/38 (13%) | 4.36 | +2.8% | obv_range_fade |
| 1h | 8/38 (21%) | 3.89 | +5.2% | TBD |
| 4h | 3/38 (8%) | 2.45 | +1.5% | TBD |

**Post-optimization (expected improvement):**
- Sharpe: +20-40% (e.g., 4.36 ? 5.2-6.1)
- Return: +30-60% (e.g., +2.8% ? +3.6-4.5%)
- Drawdown: -10-20% (e.g., -0.65% ? -0.5-0.6%)

---

## ?? **Next Steps**

1. ? Wait for discovery to complete (~90 min)
2. ? Review results, choose best timeframe
3. ? Run optimization on TOP 5 (~2-3 hours)
4. ? Generate HTML report
5. ? Validate with walk-forward
6. ? Paper trade winners (1-2 weeks)
7. ? Deploy to live trading

---

## ?? **References**

- **Optuna Documentation:** https://optuna.readthedocs.io/
- **Walk-Forward Analysis:** https://www.investopedia.com/terms/w/walk-forward-analysis.asp
- **Bayesian Optimization:** https://en.wikipedia.org/wiki/Bayesian_optimization

---

**Built with ?? by Smart-Trade**
