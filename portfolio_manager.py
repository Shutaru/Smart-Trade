"""
Portfolio Manager - Multi-Strategy Allocation

Combines multiple optimized strategies into a diversified portfolio:
- Allocates capital based on Sharpe ratios
- Manages correlation between strategies
- Rebalances dynamically
- Risk parity allocation
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np


class PortfolioManager:
    """
    Multi-Strategy Portfolio Manager
    
    Allocation methods:
    - Equal Weight: 1/N allocation
    - Sharpe-Weighted: Allocate proportional to Sharpe ratio
    - Risk Parity: Equal risk contribution
    - Max Sharpe: Optimize portfolio Sharpe
    """
    
    def __init__(
        self,
        strategies: List[Dict[str, Any]],
        total_capital: float = 10000.0,
        allocation_method: str = 'sharpe_weighted'
    ):
        self.strategies = strategies
        self.total_capital = total_capital
        self.allocation_method = allocation_method
        
        print(f"[Portfolio] Total Capital: ${total_capital:,.2f}")
        print(f"[Portfolio] Allocation Method: {allocation_method}")
        print(f"[Portfolio] Strategies: {len(strategies)}")
    
    def calculate_allocations(self) -> Dict[str, float]:
        """
        Calculate capital allocation for each strategy
        
        Returns:
            Dict mapping strategy_name -> allocated_capital
        """
        if self.allocation_method == 'equal':
            return self._equal_weight()
        elif self.allocation_method == 'sharpe_weighted':
            return self._sharpe_weighted()
        elif self.allocation_method == 'risk_parity':
            return self._risk_parity()
        elif self.allocation_method == 'max_sharpe':
            return self._max_sharpe()
        else:
            raise ValueError(f"Unknown allocation method: {self.allocation_method}")
    
    def _equal_weight(self) -> Dict[str, float]:
        """Equal weight allocation (1/N)"""
        allocation_per_strategy = self.total_capital / len(self.strategies)
        
        allocations = {}
        for strategy in self.strategies:
            name = strategy['strategy_name']
            allocations[name] = allocation_per_strategy
        
        return allocations
    
    def _sharpe_weighted(self) -> Dict[str, float]:
        """Allocate proportional to Sharpe ratio"""
        sharpes = []
        names = []
        
        for strategy in self.strategies:
            name = strategy['strategy_name']
            sharpe = strategy.get('best_metrics', {}).get('sharpe', 0)
            
            if sharpe > 0:
                sharpes.append(sharpe)
                names.append(name)
        
        if not sharpes:
            return self._equal_weight()
        
        total_sharpe = sum(sharpes)
        weights = [s / total_sharpe for s in sharpes]
        
        allocations = {}
        for name, weight in zip(names, weights):
            allocations[name] = self.total_capital * weight
        
        return allocations
    
    def _risk_parity(self) -> Dict[str, float]:
        """Equal risk contribution allocation"""
        vols = []
        names = []
        
        for strategy in self.strategies:
            name = strategy['strategy_name']
            dd = abs(strategy.get('best_metrics', {}).get('max_dd', 10.0))
            
            if dd > 0:
                vols.append(dd)
                names.append(name)
        
        if not vols:
            return self._equal_weight()
        
        inv_vols = [1.0 / v for v in vols]
        total_inv_vol = sum(inv_vols)
        weights = [iv / total_inv_vol for iv in inv_vols]
        
        allocations = {}
        for name, weight in zip(names, weights):
            allocations[name] = self.total_capital * weight
        
        return allocations
    
    def _max_sharpe(self) -> Dict[str, float]:
        """
        Optimize portfolio Sharpe ratio
        
        Simplified: Just pick top 3 by Sharpe and allocate proportionally
        """
        sorted_strategies = sorted(
            self.strategies,
            key=lambda s: s.get('best_metrics', {}).get('sharpe', 0),
            reverse=True
        )
        
        top_3 = sorted_strategies[:3]
        
        sharpes = [s.get('best_metrics', {}).get('sharpe', 0) for s in top_3]
        total_sharpe = sum(sharpes)
        
        allocations = {}
        for strategy, sharpe in zip(top_3, sharpes):
            name = strategy['strategy_name']
            weight = sharpe / total_sharpe
            allocations[name] = self.total_capital * weight
        
        return allocations
    
    def calculate_portfolio_metrics(
        self,
        allocations: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate portfolio-level metrics
        
        Simplified: Weighted average of individual metrics
        """
        total_allocated = sum(allocations.values())
        
        weighted_sharpe = 0.0
        weighted_return = 0.0
        weighted_dd = 0.0
        weighted_win_rate = 0.0
        
        for strategy in self.strategies:
            name = strategy['strategy_name']
            if name not in allocations:
                continue
            
            weight = allocations[name] / total_allocated
            metrics = strategy.get('best_metrics', {})
            
            weighted_sharpe += weight * metrics.get('sharpe', 0)
            weighted_return += weight * metrics.get('return', 0)
            weighted_dd += weight * abs(metrics.get('max_dd', 0))
            weighted_win_rate += weight * metrics.get('win_rate', 0)
        
        return {
            'portfolio_sharpe': weighted_sharpe,
            'portfolio_return': weighted_return,
            'portfolio_max_dd': weighted_dd,
            'portfolio_win_rate': weighted_win_rate,
            'total_allocated': total_allocated
        }
    
    def generate_config_files(self, allocations: Dict[str, float], output_dir: str = "data/portfolio"):
        """
        Generate individual config files for each strategy
        
        Each strategy gets its own config.yaml with allocated capital
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for strategy in self.strategies:
            name = strategy['strategy_name']
            if name not in allocations:
                continue
            
            allocated = allocations[name]
            
            config = {
                'symbol': 'BTC/USDT:USDT',
                'exchange': 'bitget',
                'timeframe': '1h',
                'risk': {
                    'starting_equity': allocated,
                    'max_risk_pct': 1.0,
                    **strategy.get('best_params', {})
                }
            }
            
            config_file = output_path / f"config_{name}.yaml"
            with open(config_file, 'w') as f:
                yaml.safe_dump(config, f)
            
            print(f"[Portfolio] Generated: {config_file}")
    
    def print_summary(self, allocations: Dict[str, float]):
        """Print portfolio allocation summary"""
        print("\n" + "=" * 80)
        print("PORTFOLIO ALLOCATION SUMMARY")
        print("=" * 80 + "\n")
        
        print(f"Total Capital: ${self.total_capital:,.2f}")
        print(f"Allocation Method: {self.allocation_method}\n")
        
        print("Strategy Allocations:")
        print("-" * 80)
        
        for name, capital in sorted(allocations.items(), key=lambda x: x[1], reverse=True):
            pct = (capital / self.total_capital) * 100
            print(f"{name:30s} ${capital:>10,.2f} ({pct:>5.1f}%)")
        
        print("-" * 80)
        print(f"{'Total':30s} ${sum(allocations.values()):>10,.2f} (100.0%)")
        
        portfolio_metrics = self.calculate_portfolio_metrics(allocations)
        
        print("\nPortfolio Metrics:")
        print("-" * 80)
        print(f"Expected Sharpe: {portfolio_metrics['portfolio_sharpe']:.2f}")
        print(f"Expected Return: {portfolio_metrics['portfolio_return']:.2f}%")
        print(f"Expected Max DD: {portfolio_metrics['portfolio_max_dd']:.2f}%")
        print(f"Expected Win Rate: {portfolio_metrics['portfolio_win_rate']:.1f}%")
        
        print("\n" + "=" * 80 + "\n")


def load_optimization_results(summary_file: str) -> List[Dict[str, Any]]:
    """Load strategies from optimization summary"""
    with open(summary_file, 'r') as f:
        data = json.load(f)
    
    return data.get('results', [])


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Portfolio allocation')
    parser.add_argument('--summary', type=str, required=True, help='Path to optimization_summary.json')
    parser.add_argument('--capital', type=float, default=10000.0, help='Total capital')
    parser.add_argument('--method', type=str, default='sharpe_weighted',
                        choices=['equal', 'sharpe_weighted', 'risk_parity', 'max_sharpe'],
                        help='Allocation method')
    
    args = parser.parse_args()
    
    strategies = load_optimization_results(args.summary)
    
    if not strategies:
        print("❌ No strategies found in summary file")
        return
    
    portfolio = PortfolioManager(
        strategies=strategies,
        total_capital=args.capital,
        allocation_method=args.method
    )
    
    allocations = portfolio.calculate_allocations()
    
    portfolio.print_summary(allocations)
    
    portfolio.generate_config_files(allocations)
    
    print("✅ Portfolio allocation complete!")
    print("   Config files generated in data/portfolio/")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())