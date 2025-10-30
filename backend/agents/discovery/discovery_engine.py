"""
Strategy Discovery Engine

Runs multiple backtests in parallel to discover optimal strategies.
Uses asyncio for concurrent execution.
"""

import asyncio
import time
import os
import subprocess
import json
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path

from .strategy_catalog import StrategyCatalog, StrategyTemplate
from .ranker import StrategyRanker, StrategyMetrics


class StrategyDiscoveryEngine:
    """
    Automated strategy discovery system
    
    Flow:
    1. Generate strategy candidates (LLM-guided combinations)
    2. Run backtests in parallel (asyncio)
    3. Collect metrics from each backtest
    4. Rank strategies using composite score
    5. Return top N strategies
    """
    
    def __init__(self, config_path: str = "config.yaml", max_parallel: int = 5):
        """
        Initialize discovery engine
        
        Args:
            config_path: Path to base config file
            max_parallel: Max number of parallel backtests
        """
        self.config_path = config_path
        self.max_parallel = max_parallel
        self.catalog = StrategyCatalog()
        self.ranker = StrategyRanker()
        
        # Load base config
        with open(config_path, 'r') as f:
            self.base_config = yaml.safe_load(f)
        
        print(f"[StrategyDiscovery] Initialized with {len(self.catalog.INDICATORS)} indicators")
    
    async def run_backtest(self, strategy_name: str, strategy_config: Dict[str, Any]) -> Optional[StrategyMetrics]:
        """
        Run single backtest asynchronously
        
        Args:
            strategy_name: Name of strategy
            strategy_config: Strategy configuration (indicators, params)
        
        Returns:
            Strategy metrics or None if failed
        """
        
        try:
            print(f"[Discovery] Running backtest: {strategy_name}")
            
            # Create temporary config for this strategy
            temp_config = self.base_config.copy()
            temp_config['risk'].update(strategy_config.get('risk', {}))
            
            # Write temp config
            temp_config_path = f"data/discovery/config_{strategy_name}.yaml"
            os.makedirs("data/discovery", exist_ok=True)
            
            with open(temp_config_path, 'w') as f:
                yaml.safe_dump(temp_config, f)
            
            # Run backtest subprocess
            cmd = [
                "python", "backtest.py",
                "--days", "365",
                "--progress-file", f"data/discovery/progress_{strategy_name}.json"
            ]
            
            # Set temp config as active (hack: backup original, use temp, restore)
            original_config_backup = "config.yaml.backup"
            os.rename("config.yaml", original_config_backup)
            os.rename(temp_config_path, "config.yaml")
            
            # Run backtest
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Restore original config
            os.rename("config.yaml", temp_config_path)
            os.rename(original_config_backup, "config.yaml")
            
            if process.returncode != 0:
                print(f"[Discovery] Backtest failed: {strategy_name}")
                print(f"Error: {stderr.decode()}")
                return None
            
            # Parse results
            try:
                result_json = json.loads(stdout.decode().strip().split('\n')[-1])
            except:
                print(f"[Discovery] Failed to parse results: {strategy_name}")
                return None
            
            # Extract metrics
            metrics = StrategyMetrics(
                strategy_name=strategy_name,
                total_return_pct=result_json.get('ret_tot_pct', 0.0),
                cagr=result_json.get('ret_tot_pct', 0.0),  # Simplified CAGR
                sharpe_ratio=result_json.get('sharpe_ann', 0.0),
                sortino_ratio=result_json.get('sharpe_ann', 0.0) * 1.2,  # Estimate
                calmar_ratio=result_json.get('ret_tot_pct', 0.0) / max(1, abs(result_json.get('maxdd_pct', 1))),
                max_drawdown_pct=result_json.get('maxdd_pct', 0.0),
                avg_drawdown_pct=result_json.get('maxdd_pct', 0.0) * 0.5,  # Estimate
                volatility_annual_pct=abs(result_json.get('ret_tot_pct', 0.0)) * 0.8,  # Estimate
                total_trades=result_json.get('trades', 0),
                win_rate_pct=result_json.get('win_rate_pct', 0.0),
                profit_factor=result_json.get('profit_factor', 0.0),
                avg_win_pct=2.5,  # Placeholder
                avg_loss_pct=-1.5,  # Placeholder
                consecutive_wins=5,  # Placeholder
                consecutive_losses=3,  # Placeholder
                recovery_factor=result_json.get('ret_tot_pct', 0.0) / max(1, abs(result_json.get('maxdd_pct', 1)))
            )
            
            print(f"[Discovery] ✅ {strategy_name}: Score={self.ranker.calculate_composite_score(metrics):.4f}")
            
            return metrics
        
        except Exception as e:
            print(f"[Discovery] Error running backtest {strategy_name}: {e}")
            return None
    
    async def discover_strategies(self, num_strategies: int = 10) -> List[StrategyMetrics]:
        """
        Discover optimal strategies by running parallel backtests
        
        Args:
            num_strategies: Number of strategy candidates to test
        
        Returns:
            List of strategy metrics (ranked)
        """
        
        print(f"\n{'='*80}")
        print(f"🔍 STRATEGY DISCOVERY ENGINE")
        print(f"{'='*80}")
        print(f"Testing {num_strategies} strategy candidates...")
        print(f"Max parallel: {self.max_parallel}")
        print(f"")
        
        # Generate strategy candidates
        strategy_candidates = StrategyTemplate.generate_combinations()[:num_strategies]
        
        print(f"📊 Strategy Candidates:")
        for i, candidate in enumerate(strategy_candidates, 1):
            print(f"  {i}. {candidate['name']}")
            print(f"     Indicators: {', '.join(candidate['indicators'])}")
        print(f"")
        
        # Run backtests in parallel (with semaphore to limit concurrency)
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def run_with_semaphore(strategy):
            async with semaphore:
                return await self.run_backtest(
                    strategy['name'],
                    {'indicators': strategy['indicators']}
                )
        
        start_time = time.time()
        
        tasks = [run_with_semaphore(candidate) for candidate in strategy_candidates]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Filter out None results (failed backtests)
        valid_results = [r for r in results if r is not None]
        
        print(f"\n{'='*80}")
        print(f"✅ Discovery Complete")
        print(f"{'='*80}")
        print(f"Time elapsed: {elapsed:.1f}s")
        print(f"Successful backtests: {len(valid_results)}/{num_strategies}")
        print(f"")
        
        # Rank strategies
        ranked_strategies = self.ranker.rank_strategies(valid_results)
        
        # Print ranking report
        print(self.ranker.format_report(ranked_strategies[:5]))
        
        return ranked_strategies
    
    def get_top_strategies(self, n: int = 3) -> List[StrategyMetrics]:
        """
        Run discovery and return top N strategies
        
        Args:
            n: Number of top strategies to return
        
        Returns:
            Top N strategies
        """
        
        # Run discovery (must be called in async context)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context
            task = asyncio.create_task(self.discover_strategies())
            strategies = loop.run_until_complete(task)
        else:
            # Create new event loop
            strategies = asyncio.run(self.discover_strategies())
        
        return self.ranker.get_top_n(strategies, n=n)


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """CLI entry point"""
    
    print("🤖 Strategy Discovery Engine v1.0")
    print("")
    
    # Initialize engine
    engine = StrategyDiscoveryEngine(
        config_path="config.yaml",
        max_parallel=3  # Adjust based on system resources
    )
    
    # Discover strategies
    strategies = await engine.discover_strategies(num_strategies=10)
    
    # Get top 3
    top3 = engine.ranker.get_top_n(strategies, n=3)
    
    print("\n" + "="*80)
    print("🏆 TOP 3 STRATEGIES FOR OPTIMIZATION")
    print("="*80)
    
    for i, strategy in enumerate(top3, 1):
        print(f"\n#{i} {strategy.strategy_name}")
        print(f"   Composite Score: {strategy.composite_score:.4f}")
        print(f"   Return: {strategy.total_return_pct:+.2f}%")
        print(f"   Max DD: {strategy.max_drawdown_pct:.2f}%")
        print(f"   Sharpe: {strategy.sharpe_ratio:.2f}")
        print(f"   Win Rate: {strategy.win_rate_pct:.1f}%")
    
    print("\n✅ Discovery complete. Use these strategies for optimization phase.")


if __name__ == '__main__':
    asyncio.run(main())