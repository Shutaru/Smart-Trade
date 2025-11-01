"""
Strategy Discovery & Optimization Orchestrator

Workflow:
1. Test all 38 strategies (baseline)
2. Rank by performance
3. Optimize top N strategies
4. Select best for paper/live trading
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import time
from datetime import datetime

from strategies.registry import ALL_STRATEGIES, STRATEGY_METADATA
from optimization.optimizer_dynamic import DynamicOptimizer
from optimization.backtest_with_params import run_backtest_with_params
from optimization.parameter_ranges import get_default_parameters_for_strategy
from core.data_loader import load_data


@dataclass
class StrategyResult:
    """Result from strategy evaluation"""
    strategy_name: str
    symbol: str
    baseline_score: float
    baseline_metrics: Dict[str, float]
    optimized_score: float = None
    optimized_params: Dict[str, Any] = None
    optimized_metrics: Dict[str, float] = None
    duration_seconds: float = 0.0
    rank: int = None


class StrategyOrchestrator:
    """
    Orchestrates strategy discovery, optimization and deployment
    """
    
    def __init__(
        self,
        symbols: List[str],
        exchange: str = 'bitget',
        timeframe: str = '5m',
        days: int = 90,
        optimization_trials: int = 50,
        top_n_to_optimize: int = 5
    ):
        """
        Initialize orchestrator
        
        Args:
            symbols: List of symbols to trade (e.g., ['BTC/USDT:USDT', 'ETH/USDT:USDT'])
            exchange: Exchange name
            timeframe: Candle timeframe
            days: Days of historical data
            optimization_trials: Trials per strategy optimization
            top_n_to_optimize: Number of top strategies to optimize
        """
        self.symbols = symbols
        self.exchange = exchange
        self.timeframe = timeframe
        self.days = days
        self.optimization_trials = optimization_trials
        self.top_n_to_optimize = top_n_to_optimize
        
        # Results storage
        self.results: Dict[str, List[StrategyResult]] = {}  # symbol -> [results]
        self.best_strategies: Dict[str, StrategyResult] = {}  # symbol -> best result
        
        # Progress tracking
        self.total_steps = 0
        self.current_step = 0
        self.status = "idle"
    
    def run_discovery_for_symbol(self, symbol: str) -> List[StrategyResult]:
        """
        Run full discovery pipeline for a single symbol
        
        Steps:
        1. Load data
        2. Test all 38 strategies (baseline)
        3. Rank strategies
        4. Optimize top N
        5. Select best
        
        Returns:
            List of StrategyResult objects (sorted by final score)
        """
        
        print(f"\n{'='*80}")
        print(f"🔍 STRATEGY DISCOVERY: {symbol}")
        print(f"{'='*80}\n")
        
        # Step 1: Load data
        print(f"[1/5] Loading data for {symbol}...")
        start_time = time.time()
        
        df, metadata = load_data(
            exchange=self.exchange,
            symbol=symbol,
            timeframe=self.timeframe,
            days=self.days,
            auto_fetch=True
        )
        
        print(f"✅ Loaded {len(df)} candles from {metadata['source']}")
        print()
        
        # Step 2: Test all 38 strategies (baseline)
        print(f"[2/5] Testing all 38 strategies (baseline)...")
        baseline_results = self._test_all_strategies_baseline(symbol, df)
        
        print(f"✅ Tested 38 strategies in {time.time() - start_time:.1f}s")
        print()
        
        # Step 3: Rank strategies
        print(f"[3/5] Ranking strategies...")
        ranked = sorted(baseline_results, key=lambda x: x.baseline_score, reverse=True)
        
        for i, result in enumerate(ranked[:10], 1):
            result.rank = i
            print(f"  #{i:2d} {result.strategy_name:35s} Score: {result.baseline_score:>7.2f} | Profit: {result.baseline_metrics['total_profit']:>6.2f}%")
        
        print()
        
        # Step 4: Optimize top N
        print(f"[4/5] Optimizing top {self.top_n_to_optimize} strategies...")
        top_strategies = ranked[:self.top_n_to_optimize]
        
        optimized_results = []
        for i, result in enumerate(top_strategies, 1):
            print(f"\n  [{i}/{self.top_n_to_optimize}] Optimizing {result.strategy_name}...")
            
            optimized = self._optimize_strategy(symbol, result.strategy_name, df)
            
            if optimized:
                result.optimized_score = optimized['score']
                result.optimized_params = optimized['params']
                result.optimized_metrics = optimized['metrics']
                
                improvement = result.optimized_score - result.baseline_score
                print(f"       ✅ Score: {result.baseline_score:.2f} → {result.optimized_score:.2f} (+{improvement:.2f})")
            else:
                print(f"       ⚠️  Optimization failed, keeping baseline")
            
            optimized_results.append(result)
        
        print()
        
        # Step 5: Select best optimized strategy
        print(f"[5/5] Selecting best strategy...")
        
        # Re-rank by optimized score (or baseline if not optimized)
        final_ranked = sorted(
            optimized_results,
            key=lambda x: x.optimized_score if x.optimized_score else x.baseline_score,
            reverse=True
        )
        
        best = final_ranked[0]
        
        print(f"")
        print(f"🏆 BEST STRATEGY: {best.strategy_name}")
        print(f"   Baseline:  {best.baseline_metrics['total_profit']:>6.2f}% profit | {best.baseline_score:>7.2f} score")
        if best.optimized_score:
            print(f"   Optimized: {best.optimized_metrics['total_profit']:>6.2f}% profit | {best.optimized_score:>7.2f} score")
            print(f"   Improvement: +{best.optimized_score - best.baseline_score:.2f} score")
        print()
        
        # Store results
        self.results[symbol] = final_ranked
        self.best_strategies[symbol] = best
        
        return final_ranked
    
    def _test_all_strategies_baseline(self, symbol: str, df: pd.DataFrame) -> List[StrategyResult]:
        """
        Test all 38 strategies with default parameters (baseline)
        
        Returns:
            List of StrategyResult objects
        """
        
        results = []
        
        for i, (strategy_name, strategy_fn) in enumerate(ALL_STRATEGIES.items(), 1):
            try:
                # Get default parameters
                metadata = STRATEGY_METADATA.get(strategy_name, {})
                params = get_default_parameters_for_strategy(strategy_name, metadata)
                
                # Add default exit params
                params.update({
                    'exit_method': 'atr_trailing',
                    'tp_rr_ratio': 2.0,
                    'sl_atr_mult': 1.5,
                    'time_stop_bars': 144
                })
                
                # Run backtest
                metrics = run_backtest_with_params(df, strategy_name, params, use_cache=True)
                
                # Calculate score (PROFIT-FIRST v5)
                score = self._calculate_score(metrics)
                
                result = StrategyResult(
                    strategy_name=strategy_name,
                    symbol=symbol,
                    baseline_score=score,
                    baseline_metrics=metrics
                )
                
                results.append(result)
                
                # Progress
                if i % 10 == 0:
                    print(f"   Progress: {i}/38 strategies tested...")
            
            except Exception as e:
                print(f"   ⚠️  {strategy_name}: {str(e)[:50]}")
                continue
        
        return results
    
    def _optimize_strategy(
        self,
        symbol: str,
        strategy_name: str,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Optimize a single strategy
        
        Returns:
            Dict with 'score', 'params', 'metrics' or None if failed
        """
        
        try:
            optimizer = DynamicOptimizer(
                strategy_name=strategy_name,
                df=df,
                n_trials=self.optimization_trials,
                use_cache=True
            )
            
            results = optimizer.optimize(
                sampler='TPE',
                pruner='Median',
                show_progress=False  # Silent mode
            )
            
            return {
                'score': results['best_score'],
                'params': results['best_params'],
                'metrics': results['best_metrics']
            }
        
        except Exception as e:
            print(f"       Error: {e}")
            return None
    
    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate PROFIT-FIRST v5 score
        
        95% Return + 2.5% Sharpe + 1.25% Sortino + 1.25% WinRate
        """
        
        # Check constraints
        if metrics['trades'] < 5:
            return -999.0
        
        if abs(metrics['max_dd']) > 50:
            return -999.0
        
        # Score components
        return_component = 0.95 * metrics['total_profit']
        
        sharpe_normalized = max(0.0, min(metrics['sharpe'] / 2.0, 1.0))
        sharpe_component = 2.5 * sharpe_normalized
        
        # Use win_rate as proxy for sortino
        sortino_component = 1.25 * (metrics['win_rate'] / 100.0)
        
        win_rate_component = 1.25 * (metrics['win_rate'] / 100.0)
        
        score = (
            return_component +
            sharpe_component +
            sortino_component +
            win_rate_component
        )
        
        return score
    
    def run_full_discovery(self) -> Dict[str, StrategyResult]:
        """
        Run discovery for all symbols
        
        Returns:
            Dict mapping symbol -> best StrategyResult
        """
        
        print(f"\n{'='*80}")
        print(f"🚀 FULL STRATEGY DISCOVERY")
        print(f"{'='*80}")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Exchange: {self.exchange}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Days: {self.days}")
        print(f"Optimization trials: {self.optimization_trials}")
        print(f"Top N to optimize: {self.top_n_to_optimize}")
        print(f"{'='*80}\n")
        
        self.status = "running"
        start_time = time.time()
        
        # Process each symbol
        for i, symbol in enumerate(self.symbols, 1):
            print(f"\n[SYMBOL {i}/{len(self.symbols)}] Processing {symbol}...")
            
            try:
                self.run_discovery_for_symbol(symbol)
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
                import traceback
                traceback.print_exc()
        
        elapsed = time.time() - start_time
        
        # Summary
        print(f"\n{'='*80}")
        print(f"✅ DISCOVERY COMPLETE")
        print(f"{'='*80}")
        print(f"Total time: {elapsed:.1f}s ({elapsed/len(self.symbols):.1f}s per symbol)")
        print()
        
        for symbol, best in self.best_strategies.items():
            profit = best.optimized_metrics['total_profit'] if best.optimized_metrics else best.baseline_metrics['total_profit']
            score = best.optimized_score if best.optimized_score else best.baseline_score
            
            print(f"  {symbol:20s} → {best.strategy_name:30s} | {profit:>6.2f}% | Score: {score:>7.2f}")
        
        print(f"\n{'='*80}\n")
        
        self.status = "completed"
        
        return self.best_strategies
    
    def export_for_paper_trade(self) -> List[Dict[str, Any]]:
        """
        Export best strategies in format for paper trading
        
        Returns:
            List of configs for paper trading
        """
        
        configs = []
        
        for symbol, best in self.best_strategies.items():
            config = {
                'symbol': symbol,
                'strategy': best.strategy_name,
                'params': best.optimized_params if best.optimized_params else {},
                'metadata': {
                    'baseline_profit': best.baseline_metrics['total_profit'],
                    'optimized_profit': best.optimized_metrics['total_profit'] if best.optimized_metrics else None,
                    'score': best.optimized_score if best.optimized_score else best.baseline_score,
                    'discovered_at': datetime.now().isoformat()
                }
            }
            
            configs.append(config)
        
        return configs


if __name__ == '__main__':
    print("✅ Testing Strategy Orchestrator...")
    
    # Test with multiple symbols
    orchestrator = StrategyOrchestrator(
        symbols=['BTC/USDT:USDT', 'ETH/USDT:USDT'],
        days=7,  # Short for testing
        optimization_trials=10,  # Few trials for testing
        top_n_to_optimize=3  # Only top 3
    )
    
    # Run discovery
    best_strategies = orchestrator.run_full_discovery()
    
    # Export for paper trading
    paper_trade_configs = orchestrator.export_for_paper_trade()
    
    print("📊 Paper Trade Configs:")
    import json
    print(json.dumps(paper_trade_configs, indent=2))
    
    print("\n✅ Orchestrator test complete!")