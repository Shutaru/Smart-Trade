"""
Backtest Engine with Dynamic Parameters - CORRECTED VERSION

Integrates dynamic indicators + cache + mapper + backtest engine.
Works for ALL 38 strategies with correct indicator names.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.indicators_dynamic import calculate_all_indicators
from core.indicator_cache import get_cache
from strategies.registry import get_strategy, STRATEGY_METADATA
from optimization.strategy_param_mapper import (
    merge_user_params_with_defaults,
    ensure_required_indicators,
    get_required_params_for_strategy
)


def run_backtest_with_params(
    df: pd.DataFrame,
    strategy_name: str,
    params: Dict[str, Any],
    use_cache: bool = True
) -> Dict[str, float]:
    """
    Run backtest with dynamic parameters - CORRECTED VERSION
    
    Args:
        df: OHLCV DataFrame
        strategy_name: Name of strategy (e.g., 'bollinger_mean_reversion')
        params: Parameter dictionary (indicator params + exit params)
        use_cache: Whether to use indicator cache (default: True)
    
    Returns:
        Dictionary with backtest metrics
    """
    
    # Step 1: Merge user params with strategy defaults
    metadata = STRATEGY_METADATA.get(strategy_name, {})
    complete_params = merge_user_params_with_defaults(params, strategy_name, metadata)
    
    # Step 2: Calculate indicators with cache
    cache = get_cache()
    
    # Create cache key from complete params (not user params)
    indicator_params = {k: v for k, v in complete_params.items() 
                       if k not in ['exit_method', 'tp_rr_ratio', 'sl_atr_mult', 
                                   'breakeven_r', 'trail_atr_mult', 'time_stop_bars']}
    
    if use_cache:
        indicators = cache.get(df, indicator_params)
        if indicators is None:
            # Cache miss - calculate
            indicators = calculate_all_indicators(df, indicator_params)
            cache.set(df, indicator_params, indicators)
    else:
        # No cache
        indicators = calculate_all_indicators(df, indicator_params)
    
    # Step 3: Ensure required indicators are present with correct names
    indicators = ensure_required_indicators(indicators, strategy_name)
    
    # Step 4: Convert indicators dict to DataFrame
    indicators_df = pd.DataFrame(indicators, index=df.index)
    
    # Step 5: Merge with OHLCV data
    data = df.copy()
    for col in indicators_df.columns:
        data[col] = indicators_df[col]
    
    # Step 6: Get strategy function
    strategy_fn = get_strategy(strategy_name)
    if strategy_fn is None:
        raise ValueError(f"Strategy '{strategy_name}' not found")
    
    # Step 7: Run simple backtest simulation
    metrics = _run_simple_backtest(data, strategy_fn, complete_params)
    
    return metrics


def _run_simple_backtest(
    data: pd.DataFrame,
    strategy_fn: callable,
    params: Dict[str, Any]
) -> Dict[str, float]:
    """
    Simple backtest implementation - IMPROVED VERSION
    
    This is a simplified version for optimization testing.
    For production, use the full backtest engine.
    """
    
    # Extract exit parameters
    exit_method = params.get('exit_method', 'atr_fixed')
    tp_rr_ratio = params.get('tp_rr_ratio', 2.0)
    sl_atr_mult = params.get('sl_atr_mult', 1.5)
    
    # Initialize
    trades = []
    equity = 10000.0
    position = None
    
    # Iterate through bars
    for i in range(200, len(data)):  # Skip warmup period
        try:
            bar = {
                'open': data['open'].iloc[i],
                'high': data['high'].iloc[i],
                'low': data['low'].iloc[i],
                'close': data['close'].iloc[i],
                'volume': data['volume'].iloc[i]
            }
            
            # Get indicators at this bar
            ind = {}
            for col in data.columns:
                if col not in ['open', 'high', 'low', 'close', 'volume']:
                    val = data[col].iloc[i]
                    ind[col] = val if not pd.isna(val) else 0
            
            state = {}
            
            # Check for exit
            if position is not None:
                # Simple exit logic
                current_price = bar['close']
                entry_price = position['entry_price']
                side = position['side']
                
                # Calculate P&L
                if side == 'LONG':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100
                
                # Get ATR for exit calculation
                atr = ind.get('atr', 0)
                if atr == 0:
                    atr = entry_price * 0.02  # Fallback: 2% of price
                
                # Check TP/SL
                tp_threshold = tp_rr_ratio * (sl_atr_mult * atr / entry_price * 100)
                sl_threshold = -(sl_atr_mult * atr / entry_price * 100)
                
                # Time-based exit
                bars_in_trade = i - position['entry_bar']
                max_bars = params.get('time_stop_bars', 144)
                
                if pnl_pct >= tp_threshold or pnl_pct <= sl_threshold or bars_in_trade >= max_bars:
                    # Close position
                    equity = equity * (1 + pnl_pct / 100)
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl_pct': pnl_pct,
                        'side': side,
                        'bars_held': bars_in_trade
                    })
                    position = None
            
            # Check for entry
            if position is None:
                try:
                    signal = strategy_fn(bar, ind, state, params)
                    
                    if signal is not None and isinstance(signal, dict):
                        side = signal.get('side')
                        if side in ['LONG', 'SHORT']:
                            position = {
                                'side': side,
                                'entry_price': bar['close'],
                                'entry_bar': i
                            }
                except Exception as e:
                    # Strategy error - skip this bar
                    pass
        
        except Exception as e:
            # Bar processing error - skip
            continue
    
    # Calculate metrics
    if len(trades) == 0:
        return {
            'total_profit': 0.0,
            'sharpe': 0.0,
            'max_dd': 0.0,
            'trades': 0,
            'win_rate': 0.0,
            'avg_bars_held': 0.0
        }
    
    returns = [t['pnl_pct'] for t in trades]
    total_profit = (equity - 10000) / 10000 * 100
    
    wins = [r for r in returns if r > 0]
    win_rate = len(wins) / len(returns) * 100 if returns else 0
    
    # Sharpe (simplified - annualized)
    if len(returns) > 1 and np.std(returns) > 0:
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
    else:
        sharpe = 0
    
    # Max drawdown (simplified)
    cumulative = np.cumsum(returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = cumulative - running_max
    max_dd = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
    
    # Average bars held
    avg_bars_held = np.mean([t['bars_held'] for t in trades])
    
    return {
        'total_profit': total_profit,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'trades': len(trades),
        'win_rate': win_rate,
        'avg_bars_held': avg_bars_held
    }


def objective_function(params: Dict[str, Any], df: pd.DataFrame, strategy_name: str) -> float:
    """
    Objective function for optimization - PROFIT-FIRST v5
    
    Uses same scoring as discovery engine:
    - 95% Return
    - 2.5% Sharpe (plateau at 2.0)
    - 1.25% Sortino (approximated by win_rate)
    - 1.25% Win Rate
    
    Constraints:
    - trades >= 5
    - max_dd < 50%
    
    Args:
        params: Parameter dictionary
        df: OHLCV DataFrame
        strategy_name: Strategy name
    
    Returns:
        Score (higher is better)
    """
    try:
        metrics = run_backtest_with_params(df, strategy_name, params)
        
        # Constraints (RELAXED - same as ranker.py v5)
        if metrics['trades'] < 5:
            return -999.0
        if abs(metrics['max_dd']) > 50:
            return -999.0
        
        # NO SHARPE CONSTRAINT! (crypto can have low Sharpe with good returns)
        
        # PROFIT-FIRST v5 Scoring (95-2.5-1.25-1.25)
        # 1. Return (95 points) - KING!
        return_component = 0.95 * metrics['total_profit']
        
        # 2. Sharpe (2.5 points) - Plateau at 2.0
        sharpe_normalized = max(0.0, min(metrics['sharpe'] / 2.0, 1.0))
        sharpe_component = 2.5 * sharpe_normalized
        
        # 3. Sortino approximation (1.25 points) - Use win_rate as proxy
        sortino_component = 1.25 * (metrics['win_rate'] / 100.0)
        
        # 4. Win Rate (1.25 points)
        win_rate_component = 1.25 * (metrics['win_rate'] / 100.0)
        
        score = (
            return_component +
            sharpe_component +
            sortino_component +
            win_rate_component
        )
        
        return score
    
    except Exception as e:
        # Error during backtest
        print(f"Error in backtest: {e}")
        return -999.0


if __name__ == '__main__':
    print("✅ Testing Backtest with Dynamic Parameters (CORRECTED)...")
    
    # Create test data
    dates = pd.date_range('2024-01-01', periods=1000, freq='5min')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': 42000 + np.random.randn(1000).cumsum() * 100,
        'high': 42000 + np.random.randn(1000).cumsum() * 100 + 50,
        'low': 42000 + np.random.randn(1000).cumsum() * 100 - 50,
        'close': 42000 + np.random.randn(1000).cumsum() * 100,
        'volume': np.random.randint(100, 1000, 1000)
    }, index=dates)
    
    # Test parameters (minimal - mapper will add required ones)
    params = {
        'rsi_period': 14,
        'bb_period': 20,
        'bb_std': 2.0,
        'exit_method': 'atr_trailing',
        'tp_rr_ratio': 2.0,
        'sl_atr_mult': 1.5,
        'time_stop_bars': 100
    }
    
    print("\n" + "=" * 80)
    print("TEST 1: bollinger_mean_reversion with mapper integration")
    print("=" * 80)
    
    try:
        metrics = run_backtest_with_params(df, 'bollinger_mean_reversion', params, use_cache=True)
        
        print("\n📊 Backtest Metrics:")
        print(f"  Total Profit:    {metrics['total_profit']:>8.2f}%")
        print(f"  Sharpe:          {metrics['sharpe']:>8.2f}")
        print(f"  Max DD:          {metrics['max_dd']:>8.2f}%")
        print(f"  Trades:          {metrics['trades']:>8}")
        print(f"  Win Rate:        {metrics['win_rate']:>8.2f}%")
        print(f"  Avg Bars Held:   {metrics['avg_bars_held']:>8.1f}")
        
        if metrics['trades'] > 0:
            print("\n✅ SUCCESS! Strategy generated trades!")
        else:
            print("\n⚠️  WARNING: No trades generated (may need different data)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test cache performance
    print("\n" + "=" * 80)
    print("TEST 2: Cache performance with mapper")
    print("=" * 80)
    
    import time
    
    # Clear cache
    cache = get_cache()
    cache.clear()
    
    # First run (cache miss)
    start = time.time()
    metrics1 = run_backtest_with_params(df, 'bollinger_mean_reversion', params, use_cache=True)
    time1 = time.time() - start
    
    # Second run (cache hit)
    start = time.time()
    metrics2 = run_backtest_with_params(df, 'bollinger_mean_reversion', params, use_cache=True)
    time2 = time.time() - start
    
    print(f"\n⏱️  First run (cache miss):  {time1:.4f}s")
    print(f"⏱️  Second run (cache hit):  {time2:.4f}s")
    
    if time2 < time1:
        print(f"🚀 Speedup: {time1/time2:.2f}x")
    else:
        print(f"⚠️  Cache overhead (normal for small datasets)")
    
    # Print cache stats
    cache.print_stats()
    
    # Test objective function
    print("\n" + "=" * 80)
    print("TEST 3: Objective function (PROFIT-FIRST v5)")
    print("=" * 80)
    
    score = objective_function(params, df, 'bollinger_mean_reversion')
    print(f"\n📈 Objective Score: {score:.2f}")
    
    if score > 0:
        print("✅ Score is positive!")
    elif score == -999.0:
        print("⚠️  Constraints not met (needs >=5 trades)")
    else:
        print("⚠️  Score is negative")
    
    # Test multiple strategies
    print("\n" + "=" * 80)
    print("TEST 4: Multiple strategies")
    print("=" * 80)
    
    test_strategies = [
        ('bollinger_mean_reversion', {'rsi_period': 14, 'bb_period': 20, 'bb_std': 2.0}),
        ('rsi_band_reversion', {'rsi_period': 14, 'bb_period': 20, 'bb_std': 2.0}),
    ]
    
    for strat_name, strat_params in test_strategies:
        try:
            full_params = {**strat_params, 'tp_rr_ratio': 2.0, 'sl_atr_mult': 1.5}
            metrics = run_backtest_with_params(df, strat_name, full_params, use_cache=True)
            print(f"\n✅ {strat_name:30s}: {metrics['trades']:3d} trades, {metrics['total_profit']:>7.2f}% profit")
        except Exception as e:
            print(f"\n❌ {strat_name:30s}: Error - {str(e)[:50]}")
    
    print("\n✅ All integration tests completed!")