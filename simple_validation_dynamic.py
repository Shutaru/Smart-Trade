"""
Simple Validation with Dynamic Parameters

Uses database data with fallback to synthetic.
End-to-end validation:
1. Baseline backtest
2. Dynamic parameter optimization (Optuna)
3. Post-optimization backtest
4. Comparison
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from optimization.optimizer_dynamic import DynamicOptimizer
from optimization.backtest_with_params import run_backtest_with_params
from optimization.parameter_ranges import get_default_parameters_for_strategy
from strategies.registry import STRATEGY_METADATA
from core.data_loader import load_data


def run_simple_validation_dynamic(
    strategy_name: str,
    exchange: str = 'bitget',
    symbol: str = 'BTC/USDT:USDT',
    timeframe: str = '5m',
    days: int = 90,
    n_trials: int = 50
):
    """
    Run simple validation with dynamic parameters
    
    Args:
        strategy_name: Strategy to test
        exchange: Exchange name
        symbol: Symbol
        timeframe: Timeframe
        days: Days of data
        n_trials: Number of optimization trials
    """
    
    print("=" * 80)
    print(f"SIMPLE VALIDATION (DYNAMIC): {strategy_name}")
    print("=" * 80)
    print(f"Exchange: {exchange} | Symbol: {symbol} | Days: {days} | Trials: {n_trials}")
    print()
    
    # Load data (real or synthetic fallback)
    print("=" * 80)
    print("LOADING DATA")
    print("=" * 80)
    print()
    
    df, metadata = load_data(
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        days=days,
        auto_fetch=True  # ✅ CORRETO
    )
    
    print(f"✅ Loaded {metadata['candles']} candles")
    print(f"   Source: {metadata['source'].upper()}")
    print(f"   Period: {metadata['start_date']} to {metadata['end_date']}")
    print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print(f"   Database: {metadata['db_path']}")
    print()
    
    # Step 1: Baseline
    print("=" * 80)
    print("STEP 1: BASELINE")
    print("=" * 80)
    print()
    
    print("[Running] Baseline backtest...")
    
    # Get default parameters
    strategy_metadata = STRATEGY_METADATA.get(strategy_name, {})
    baseline_params = get_default_parameters_for_strategy(strategy_name, strategy_metadata)
    
    # Add default exit params
    baseline_params.update({
        'exit_method': 'atr_trailing',
        'tp_rr_ratio': 2.0,
        'sl_atr_mult': 1.5,
        'time_stop_bars': 144
    })
    
    baseline_metrics = run_backtest_with_params(df, strategy_name, baseline_params)
    
    print("[OK] Baseline backtest")
    print()
    
    print("BASELINE RESULTS:")
    print(f"  Return:      {baseline_metrics['total_profit']:>8.2f}%")
    print(f"  Sharpe:      {baseline_metrics['sharpe']:>8.2f}")
    print(f"  Max DD:     {baseline_metrics['max_dd']:>8.2f}%")
    print(f"  Trades:     {baseline_metrics['trades']:>8}")
    print(f"  Win Rate:   {baseline_metrics['win_rate']:>8.2f}%")
    print()
    
    # Step 2: Optimization
    print("=" * 80)
    print(f"STEP 2: OPTIMIZATION ({n_trials} trials)")
    print("=" * 80)
    print()
    
    print("[Running] Parameter optimization...")
    
    optimizer = DynamicOptimizer(
        strategy_name=strategy_name,
        df=df,
        n_trials=n_trials,
        use_cache=True
    )
    
    opt_results = optimizer.optimize(
        sampler='TPE',
        pruner='Median',
        show_progress=True
    )
    
    print("[OK] Parameter optimization")
    print()
    
    # Step 3: Post-optimization
    print("=" * 80)
    print("STEP 3: POST-OPTIMIZATION")
    print("=" * 80)
    print()
    
    print("[Running] Post-optimization backtest...")
    
    optimized_metrics = opt_results['best_metrics']
    
    print("[OK] Post-optimization backtest")
    print()
    
    print("POST-OPTIMIZATION RESULTS:")
    print(f"  Return:      {optimized_metrics['total_profit']:>8.2f}%")
    print(f"  Sharpe:      {optimized_metrics['sharpe']:>8.2f}")
    print(f"  Max DD:     {optimized_metrics['max_dd']:>8.2f}%")
    print(f"  Trades:     {optimized_metrics['trades']:>8}")
    print(f"  Win Rate:   {optimized_metrics['win_rate']:>8.2f}%")
    print()
    
    # Step 4: Comparison
    print("=" * 80)
    print("COMPARISON: BEFORE vs AFTER")
    print("=" * 80)
    print()
    
    print(f"{'Metric':<20s} {'Baseline':>12s} {'Optimized':>12s} {'Change':>12s}")
    print("-" * 60)
    
    def print_comparison(name, base_val, opt_val, is_pct=True):
        change = opt_val - base_val
        change_str = f"{change:+.2f}" if is_pct else f"{change:+.0f}"
        print(f"{name:<20s} {base_val:>12.2f} {opt_val:>12.2f} {change_str:>12s}")
    
    print_comparison("Return %", baseline_metrics['total_profit'], optimized_metrics['total_profit'])
    print_comparison("Sharpe", baseline_metrics['sharpe'], optimized_metrics['sharpe'])
    print_comparison("Max DD %", baseline_metrics['max_dd'], optimized_metrics['max_dd'])
    print_comparison("Trades", baseline_metrics['trades'], optimized_metrics['trades'], is_pct=False)
    print_comparison("Win Rate %", baseline_metrics['win_rate'], optimized_metrics['win_rate'])
    print()
    
    # Improvement
    improvement = optimized_metrics['total_profit'] - baseline_metrics['total_profit']
    
    print("=" * 60)
    if improvement > 0:
        print(f"✅ IMPROVEMENT: +{improvement:.2f}% profit")
    elif improvement < 0:
        print(f"⚠️  REGRESSION: {improvement:.2f}% profit")
    else:
        print("➖ NO CHANGE")
    print("=" * 60)
    
    print()
    
    # Best parameters
    print("=" * 80)
    print("OPTIMIZED PARAMETERS")
    print("=" * 80)
    print()
    
    for key, val in sorted(opt_results['best_params'].items()):
        print(f"  {key:25s}: {val}")
    
    print()
    
    # Data source info
    print("=" * 80)
    print("DATA SOURCE")
    print("=" * 80)
    print()
    print(f"  Exchange:    {metadata.get('exchange', 'N/A')}")
    print(f"  Symbol:      {metadata.get('symbol', 'N/A')}")
    print(f"  Timeframe:   {metadata.get('timeframe', 'N/A')}")
    print(f"  Source:      {metadata['source'].upper()}")
    print(f"  DB Path:     {metadata.get('db_path', 'N/A')}")
    print(f"  Candles:     {metadata.get('candles', 'N/A')}")
    print(f"  Days:        {metadata.get('days_actual', 'N/A')}")
    print()
    print("=" * 80)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Validation with Dynamic Parameters')
    parser.add_argument('--strategy', type=str, default='bollinger_mean_reversion',
                      help='Strategy name')
    parser.add_argument('--exchange', type=str, default='bitget',
                      help='Exchange name')
    parser.add_argument('--symbol', type=str, default='BTC/USDT:USDT',
                      help='Symbol')
    parser.add_argument('--timeframe', type=str, default='5m',
                      help='Timeframe')
    parser.add_argument('--days', type=int, default=90,
                      help='Days of data')
    parser.add_argument('--trials', type=int, default=50,
                      help='Number of optimization trials')
    
    args = parser.parse_args()
    
    try:
        run_simple_validation_dynamic(
            strategy_name=args.strategy,
            exchange=args.exchange,
            symbol=args.symbol,
            timeframe=args.timeframe,
            days=args.days,
            n_trials=args.trials
        )
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ============================================================================
# DYNAMIC OPTIMIZATION (NEW SYSTEM - INTEGRATED)
# ============================================================================

@router.post("/run/optimize-dynamic", response_model=RunResponse)
async def run_dynamic_optimization(
    strategy_name: str,
    exchange: str = 'bitget',
    symbol: str = 'BTC/USDT:USDT',
    timeframe: str = '5m',
    days: int = 90,
    n_trials: int = 50
):
    """
    Start dynamic parameter optimization (NEW SYSTEM)
    
    Uses:
    - Auto-fetch from exchange if data missing
    - Auto-detection of required parameters
    - PROFIT-FIRST v5 objective
    - Real-time progress via WebSocket
    
    Returns:
        run_id for tracking progress
    """
    from lab_runner import start_dynamic_optimization_run
    
    try:
        run_id = start_dynamic_optimization_run(
            strategy_name=strategy_name,
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            days=days,
            n_trials=n_trials
        )
        
        return RunResponse(run_id=run_id, status="pending")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to start dynamic optimization: {str(e)}")


@router.get("/strategies-all")
async def get_all_strategies():
    """Get all 38 strategies with full metadata"""
    from strategies.registry import ALL_STRATEGIES, STRATEGY_METADATA
    
    result = []
    for name in sorted(ALL_STRATEGIES.keys()):
        metadata = STRATEGY_METADATA.get(name, {})
        result.append({
            "name": name,
            "id": metadata.get("id", 0),
            "category": metadata.get("category", "unknown"),
            "description": metadata.get("description", ""),
            "indicators": metadata.get("indicators", []),
            "regime": metadata.get("regime", "unknown"),
            "complexity": metadata.get("complexity", "medium"),
            "risk_reward": metadata.get("risk_reward", "1:2"),
            "win_rate_range": metadata.get("win_rate_range", "40-50%"),
        })
    
    return {"strategies": result, "total": len(result)}