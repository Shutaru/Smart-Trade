"""
Strategy Optimizer Runner - Multi-Symbol & Multi-Timeframe
"""

import sys
from pathlib import Path
import argparse

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from optimization.optimizer import StrategyOptimizer, ParameterRange, DEFAULT_RANGES


def main():
    parser = argparse.ArgumentParser(description='Strategy Optimizer')
    
    parser.add_argument('--strategy', required=True, help='Strategy name')
    parser.add_argument('--symbol', default=None, help='Symbol (e.g., ETH/USDT)')
    parser.add_argument('--exchange', default=None, help='Exchange (binance, bitget)')
    parser.add_argument('--timeframe', default=None, help='Timeframe (5m, 1h, 4h)')
    parser.add_argument('--trials', type=int, default=50, help='Trials (default: 50)')
    parser.add_argument('--parallel', type=int, default=1, help='Parallel jobs')
    parser.add_argument('--config', default='config.yaml', help='Config file')
    parser.add_argument('--days', type=int, default=365, help='Backtest days')
    parser.add_argument('--sampler', default='TPE', choices=['TPE', 'Grid'])
    
    args = parser.parse_args()
    
    print("="*80)
    print("STRATEGY OPTIMIZER - PROFIT-FIRST")
    print("="*80)
    print()
    
    # Auto-detect parameters
    strat = args.strategy.lower()
    param_ranges = []
    
    if 'rsi' in strat:
        param_ranges.extend(DEFAULT_RANGES['rsi'])
    if 'bollinger' in strat:
        param_ranges.extend(DEFAULT_RANGES['bollinger'])
    if 'cci' in strat:
        param_ranges.extend(DEFAULT_RANGES['cci'])
    if 'vwap' in strat:
        param_ranges.extend(DEFAULT_RANGES['vwap'])
    if 'stoch' in strat:
        param_ranges.extend(DEFAULT_RANGES['stochastic'])
    if 'ema' in strat:
        param_ranges.extend(DEFAULT_RANGES['ema'])
    if 'adx' in strat:
        param_ranges.extend(DEFAULT_RANGES['adx'])
    if 'atr' in strat:
        param_ranges.extend(DEFAULT_RANGES['atr'])
    
    # Always add exits
    param_ranges.extend(DEFAULT_RANGES['exits'])
    
    # Remove duplicates
    seen = set()
    unique = []
    for pr in param_ranges:
        if pr.name not in seen:
            seen.add(pr.name)
            unique.append(pr)
    param_ranges = unique
    
    if not param_ranges:
        param_ranges = DEFAULT_RANGES['exits']
    
    print(f"Strategy: {args.strategy}")
    print(f"Symbol: {args.symbol or 'from config'}")
    print(f"Exchange: {args.exchange or 'from config'}")
    print(f"Timeframe: {args.timeframe or 'from config'}")
    print(f"Trials: {args.trials}")
    print(f"Parallel: {args.parallel}")
    print(f"Parameters: {len(param_ranges)}")
    for pr in param_ranges:
        if pr.type == 'categorical':
            print(f"  - {pr.name}: {pr.choices}")
        else:
            print(f"  - {pr.name}: [{pr.low}, {pr.high}]")
    print()
    
    # Create optimizer
    optimizer = StrategyOptimizer(
        strategy_name=args.strategy,
        base_config_path=args.config,
        symbol=args.symbol,
        exchange=args.exchange,
        timeframe=args.timeframe,
        param_ranges=param_ranges,
        n_trials=args.trials
    )
    
    # Run
    try:
        results = optimizer.optimize(
            n_jobs=args.parallel,
            sampler=args.sampler,
            show_progress=True
        )
        
        print()
        print("="*80)
        print("OPTIMIZATION COMPLETE")
        print("="*80)
        print(f"Best Score: {results['best_value']:.4f}")
        print(f"Best Return: {results['best_metrics']['return']:.2f}%")
        print(f"Best Sharpe: {results['best_metrics']['sharpe']:.2f}")
        print(f"Max DD: {results['best_metrics']['max_dd']:.2f}%")
        print(f"Trades: {results['best_metrics']['trades']}")
        print(f"Win Rate: {results['best_metrics']['win_rate']:.1f}%")
        print()
        print("Best Parameters:")
        for key, value in results['best_params'].items():
            print(f"  {key}: {value}")
        print()
        print(f"Results: {optimizer.output_dir}/optimization_results.json")
        
    except KeyboardInterrupt:
        print("\nCancelled")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()