"""
Optimize Top 5 Strategies

Automatically optimizes the top 5 strategies from discovery results.
Uses PROFIT-FIRST scoring (70% return, 10% Sortino, constraints).
"""

import asyncio
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any
from strategy_optimizer import StrategyOptimizer, ParameterRange, DEFAULT_RANGES


def get_parameter_ranges_for_strategy(strategy_name: str) -> List[ParameterRange]:
    """
    Get parameter ranges for a strategy based on its indicators
    
    Maps strategy names to appropriate parameter ranges.
    Uses comprehensive ranges from DEFAULT_RANGES.
    """
    
    ranges = []
    name_lower = strategy_name.lower()
    
    # RSI strategies
    if 'rsi' in name_lower:
        ranges.extend(DEFAULT_RANGES['rsi'])
    
    # EMA strategies
    if 'ema' in name_lower or 'cross' in name_lower or 'stack' in name_lower:
        ranges.extend(DEFAULT_RANGES['ema'])
    
    # SMA strategies
    if 'sma' in name_lower:
        ranges.extend(DEFAULT_RANGES['sma'])
    
    # ADX strategies (trend strength)
    if 'adx' in name_lower or 'trend' in name_lower or 'filtered' in name_lower:
        ranges.extend(DEFAULT_RANGES['adx'])
    
    # ATR strategies (volatility/stops)
    if 'atr' in name_lower or 'trail' in name_lower or 'stop' in name_lower:
        ranges.extend(DEFAULT_RANGES['atr'])
    
    # Bollinger Bands
    if 'bollinger' in name_lower or 'bb' in name_lower or 'revert' in name_lower:
        ranges.extend(DEFAULT_RANGES['bollinger'])
    
    # MACD
    if 'macd' in name_lower:
        ranges.extend(DEFAULT_RANGES['macd'])
    
    # Stochastic
    if 'stoch' in name_lower or 'reversal' in name_lower:
        ranges.extend(DEFAULT_RANGES['stochastic'])
    
    # CCI
    if 'cci' in name_lower or 'snapback' in name_lower:
        ranges.extend(DEFAULT_RANGES['cci'])
    
    # MFI
    if 'mfi' in name_lower or 'exhaustion' in name_lower:
        ranges.extend(DEFAULT_RANGES['mfi'])
    
    # SuperTrend
    if 'supertrend' in name_lower or 'continuation' in name_lower:
        ranges.extend(DEFAULT_RANGES['supertrend'])
    
    # Donchian
    if 'donchian' in name_lower or 'breakout' in name_lower:
        ranges.extend(DEFAULT_RANGES['donchian'])
    
    # Keltner
    if 'keltner' in name_lower or 'expansion' in name_lower:
        ranges.extend(DEFAULT_RANGES['keltner'])
    
    # OBV
    if 'obv' in name_lower or 'range' in name_lower or 'slope' in name_lower:
        ranges.extend(DEFAULT_RANGES['obv'])
    
    # VWAP
    if 'vwap' in name_lower or 'reclaim' in name_lower:
        ranges.extend(DEFAULT_RANGES['vwap'])
    
    # Always add exit parameters
    ranges.extend(DEFAULT_RANGES['exits'])
    
    # If no specific ranges found, use generic set
    if not ranges or len(ranges) <= 4:  # Only exits
        ranges = [
            ParameterRange('rsi_period', 'int', low=10, high=20, step=2),
            ParameterRange('adx_threshold', 'int', low=18, high=30, step=2),
            ParameterRange('atr_sl_mult', 'float', low=1.5, high=3.0, step=0.25),
            ParameterRange('tp_rr_ratio', 'float', low=1.5, high=3.5, step=0.25),
        ]
    
    return ranges


async def optimize_strategy(
    strategy_name: str,
    n_trials: int = 30
) -> Dict[str, Any]:
    """Optimize a single strategy using PROFIT-FIRST scoring"""
    print(f"\n{'='*80}")
    print(f"OPTIMIZING: {strategy_name}")
    print(f"{'='*80}\n")
    
    # Get parameter ranges
    param_ranges = get_parameter_ranges_for_strategy(strategy_name)
    
    print(f"Parameter ranges: {len(param_ranges)}")
    for pr in param_ranges:
        if pr.type in ['int', 'float']:
            print(f"  - {pr.name}: [{pr.low}, {pr.high}]")
        else:
            print(f"  - {pr.name}: {pr.choices}")
    
    # Create optimizer
    optimizer = StrategyOptimizer(
        strategy_name=strategy_name,
        param_ranges=param_ranges,
        n_trials=n_trials
    )
    
    # Run optimization (synchronous, but wrapped in async)
    results = await asyncio.to_thread(
        optimizer.optimize,
        n_jobs=1,
        sampler='TPE',
        show_progress=True
    )
    
    return results


async def optimize_top_strategies(
    top_n: int = 5,
    n_trials_per_strategy: int = 30,
    timeframe: str = '1h'
):
    """Optimize top N strategies from discovery using PROFIT-FIRST scoring"""
    
    print("\n" + "="*100)
    print(f"🔧 OPTIMIZING TOP {top_n} STRATEGIES")
    print("="*100)
    print(f"Timeframe: {timeframe}")
    print(f"Trials per strategy: {n_trials_per_strategy}")
    print(f"Scoring: PROFIT-FIRST (70% return, 10% Sortino, 10% win rate, 5% trades, 5% DD penalty)")
    print("="*100 + "\n")
    
    # TOP 5 from 1h discovery results
    top_strategies = [
        'obv_range_fade',
        'obv_slope_break',
        'stoch_fast_reversal',
        'triple_momentum_stack',
        'adx_filtered_ema_stack'
    ]
    
    print(f"📋 Strategies to optimize:")
    for i, strat in enumerate(top_strategies, 1):
        print(f"   {i}. {strat}")
    print()
    
    # Optimize each strategy sequentially
    start_time = time.time()
    results = []
    
    for i, strategy_name in enumerate(top_strategies, 1):
        print(f"\n{'#'*100}")
        print(f"# STRATEGY {i}/{len(top_strategies)}")
        print(f"{'#'*100}\n")
        
        try:
            result = await optimize_strategy(
                strategy_name=strategy_name,
                n_trials=n_trials_per_strategy
            )
            results.append(result)
            
            print(f"\n✅ {strategy_name} optimization complete")
            print(f"   Best score: {result['best_value']:.4f}")
            
        except Exception as e:
            print(f"\n❌ Failed to optimize {strategy_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    elapsed = time.time() - start_time
    
    # Save combined results
    output_dir = Path("data") / "optimization" / f"top{top_n}_{timeframe}_{int(time.time())}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary_file = output_dir / "optimization_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'timeframe': timeframe,
            'n_strategies': len(results),
            'n_trials_per_strategy': n_trials_per_strategy,
            'scoring': 'PROFIT-FIRST (70% return, 10% Sortino, constraints)',
            'elapsed_seconds': elapsed,
            'results': results
        }, f, indent=2)
    
    # Print final summary
    print("\n" + "="*100)
    print("✅ OPTIMIZATION COMPLETE")
    print("="*100 + "\n")
    
    print(f"Optimized {len(results)}/{len(top_strategies)} strategies")
    print(f"Total time: {elapsed/60:.1f} minutes ({elapsed:.0f} seconds)")
    print(f"Results saved to: {summary_file}\n")
    
    # Print ranking
    print("📊 OPTIMIZED STRATEGIES RANKING:")
    print("-" * 100)
    
    sorted_results = sorted(results, key=lambda r: r['best_value'], reverse=True)
    
    for i, result in enumerate(sorted_results, 1):
        print(f"{i}. {result['strategy_name']}")
        print(f"   Best score: {result['best_value']:.4f}")
        print(f"   Metrics: ", end='')
        metrics = result.get('best_metrics', {})
        print(f"Return: {metrics.get('return', 0):.2f}% | ", end='')
        print(f"DD: {metrics.get('max_dd', 0):.2f}% | ", end='')
        print(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print()
    
    print("="*100 + "\n")
    
    return results


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimize top strategies from discovery')
    parser.add_argument('--top-n', type=int, default=5, help='Number of top strategies to optimize')
    parser.add_argument('--trials', type=int, default=30, help='Trials per strategy')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe (5m, 1h, 4h)')
    
    args = parser.parse_args()
    
    try:
        results = await optimize_top_strategies(
            top_n=args.top_n,
            n_trials_per_strategy=args.trials,
            timeframe=args.timeframe
        )
        
        print("\n🎉 All optimizations complete!")
        print(f"   {len(results)} strategies optimized")
        print(f"   Ready for live trading or further validation\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Optimization cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())