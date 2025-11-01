"""
Multi-Strategy Portfolio Manager

Core portfolio management system that:
- Manages multiple strategies simultaneously
- Allocates capital across strategies
- Tracks performance per strategy
- Handles risk management
- Supports dynamic rebalancing
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time
from backend.agents.discovery.ranker from strategies import core as strategyMetrics


@dataclass
class StrategyAllocation:
    """Allocation for a single strategy"""
    strategy: StrategyMetrics
    weight: float  # 0.0 to 1.0
    capital_allocated: float
    active: bool = True
    
    # Performance tracking
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    num_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # Risk metrics
    current_drawdown_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    peak_capital: float = 0.0


class MultiStrategyPortfolio:
    """
    Multi-strategy portfolio manager
    
    Manages allocation and execution across multiple strategies.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        allocation_mode: str = "balanced"
    ):
        """
        Initialize portfolio manager
        
        Args:
            initial_capital: Starting capital
            allocation_mode: 'conservative', 'balanced', 'aggressive'
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.allocation_mode = allocation_mode
        
        # Strategy allocations
        self.allocations: Dict[str, StrategyAllocation] = {}
        
        # Portfolio-level tracking
        self.total_pnl = 0.0
        self.total_trades = 0
        self.equity_curve = []
        self.started_at = None
        
        print(f"[Portfolio] Initialized with ${initial_capital:,.2f}")
        print(f"[Portfolio] Allocation mode: {allocation_mode}")
    
    def add_strategy(
        self,
        strategy_name: str,
        strategy: StrategyMetrics,
        weight: float
    ):
        """
        Add strategy to portfolio
        
        Args:
            strategy_name: Unique identifier
            strategy: Strategy metrics
            weight: Allocation weight (0.0 to 1.0)
        """
        
        capital_allocated = self.current_capital * weight
        
        allocation = StrategyAllocation(
            strategy=strategy,
            weight=weight,
            capital_allocated=capital_allocated,
            peak_capital=capital_allocated
        )
        
        self.allocations[strategy_name] = allocation
        
        print(f"[Portfolio] Added {strategy_name}: {weight*100:.1f}% (${capital_allocated:,.2f})")
    
    def setup_strategies(
        self,
        strategies: Dict[str, StrategyMetrics],
        weights: Dict[str, float]
    ):
        """
        Setup multiple strategies at once
        
        Args:
            strategies: Dict mapping category to strategy
            weights: Dict mapping category to weight
        """
        
        print(f"\n{'='*80}")
        print(f"PORTFOLIO SETUP")
        print(f"{'='*80}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Allocation Mode: {self.allocation_mode}")
        print(f"")
        
        for category, strategy in strategies.items():
            if strategy is None:
                continue
            
            weight = weights.get(category, 0.0)
            if weight > 0:
                self.add_strategy(category, strategy, weight)
        
        print(f"")
        print(f"✅ Portfolio setup complete with {len(self.allocations)} strategies")
    
    def get_portfolio_status(self) -> Dict[str, Any]:
        """
        Get current portfolio status
        
        Returns:
            Portfolio status dict
        """
        
        total_allocated = sum(a.capital_allocated for a in self.allocations.values())
        total_pnl = sum(a.realized_pnl + a.unrealized_pnl for a in self.allocations.values())
        total_trades = sum(a.num_trades for a in self.allocations.values())
        
        # Calculate win rate
        total_wins = sum(a.winning_trades for a in self.allocations.values())
        total_losses = sum(a.losing_trades for a in self.allocations.values())
        win_rate = (total_wins / max(1, total_wins + total_losses)) * 100
        
        # Calculate drawdown
        current_equity = self.initial_capital + total_pnl
        peak_equity = max(self.initial_capital, current_equity)
        drawdown_pct = ((current_equity - peak_equity) / peak_equity) * 100
        
        return {
            "initial_capital": self.initial_capital,
            "current_equity": current_equity,
            "total_pnl": total_pnl,
            "total_pnl_pct": (total_pnl / self.initial_capital) * 100,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "drawdown_pct": drawdown_pct,
            "num_strategies": len(self.allocations),
            "allocation_mode": self.allocation_mode,
            "strategies": {
                name: {
                    "weight": alloc.weight,
                    "capital": alloc.capital_allocated,
                    "pnl": alloc.realized_pnl + alloc.unrealized_pnl,
                    "pnl_pct": ((alloc.realized_pnl + alloc.unrealized_pnl) / alloc.capital_allocated) * 100,
                    "trades": alloc.num_trades,
                    "active": alloc.active
                }
                for name, alloc in self.allocations.items()
            }
        }
    
    def record_trade(
        self,
        strategy_name: str,
        pnl: float,
        is_win: bool
    ):
        """
        Record trade result for a strategy
        
        Args:
            strategy_name: Strategy identifier
            pnl: Profit/loss amount
            is_win: Whether trade was profitable
        """
        
        if strategy_name not in self.allocations:
            print(f"⚠️  Strategy {strategy_name} not found in portfolio")
            return
        
        alloc = self.allocations[strategy_name]
        
        # Update strategy metrics
        alloc.realized_pnl += pnl
        alloc.num_trades += 1
        
        if is_win:
            alloc.winning_trades += 1
        else:
            alloc.losing_trades += 1
        
        # Update capital
        alloc.capital_allocated += pnl
        
        # Update drawdown
        if alloc.capital_allocated > alloc.peak_capital:
            alloc.peak_capital = alloc.capital_allocated
            alloc.current_drawdown_pct = 0.0
        else:
            alloc.current_drawdown_pct = ((alloc.capital_allocated - alloc.peak_capital) / alloc.peak_capital) * 100
            alloc.max_drawdown_pct = min(alloc.max_drawdown_pct, alloc.current_drawdown_pct)
        
        # Update portfolio total
        self.total_pnl += pnl
        self.total_trades += 1
        self.current_capital += pnl
        
        print(f"[Portfolio] {strategy_name}: Trade #{alloc.num_trades} | PnL: ${pnl:+,.2f} | Total PnL: ${alloc.realized_pnl:+,.2f}")
    
    def check_rebalancing_needed(self, threshold_pct: float = 10.0) -> bool:
        """
        Check if portfolio rebalancing is needed
        
        Args:
            threshold_pct: Rebalance if weight drift > this %
        
        Returns:
            True if rebalancing needed
        """
        
        total_capital = sum(a.capital_allocated for a in self.allocations.values())
        
        for name, alloc in self.allocations.items():
            current_weight = alloc.capital_allocated / total_capital
            target_weight = alloc.weight
            drift_pct = abs((current_weight - target_weight) / target_weight) * 100
            
            if drift_pct > threshold_pct:
                print(f"[Portfolio] Rebalancing needed: {name} drift {drift_pct:.1f}%")
                return True
        
        return False
    
    def rebalance(self):
        """
        Rebalance portfolio to target weights
        """
        
        print(f"\n[Portfolio] Rebalancing portfolio...")
        
        total_capital = sum(a.capital_allocated for a in self.allocations.values())
        
        for name, alloc in self.allocations.items():
            target_capital = total_capital * alloc.weight
            adjustment = target_capital - alloc.capital_allocated
            
            alloc.capital_allocated = target_capital
            
            print(f"  {name}: ${adjustment:+,.2f} → ${target_capital:,.2f} ({alloc.weight*100:.1f}%)")
        
        print(f"✅ Rebalancing complete")
    
    def disable_strategy(self, strategy_name: str, reason: str = ""):
        """
        Disable underperforming strategy
        
        Args:
            strategy_name: Strategy to disable
            reason: Reason for disabling
        """
        
        if strategy_name not in self.allocations:
            return
        
        self.allocations[strategy_name].active = False
        
        print(f"[Portfolio] ❌ Disabled {strategy_name}: {reason}")
    
    def get_performance_report(self) -> str:
        """
        Generate performance report
        
        Returns:
            Formatted report string
        """
        
        status = self.get_portfolio_status()
        
        report = []
        report.append("=" * 80)
        report.append("MULTI-STRATEGY PORTFOLIO PERFORMANCE")
        report.append("=" * 80)
        report.append("")
        report.append(f"💰 Portfolio Summary:")
        report.append(f"  Initial Capital: ${status['initial_capital']:,.2f}")
        report.append(f"  Current Equity:  ${status['current_equity']:,.2f}")
        report.append(f"  Total PnL:       ${status['total_pnl']:+,.2f} ({status['total_pnl_pct']:+.2f}%)")
        report.append(f"  Total Trades:    {status['total_trades']}")
        report.append(f"  Win Rate:        {status['win_rate']:.1f}%")
        report.append(f"  Drawdown:        {status['drawdown_pct']:.2f}%")
        report.append(f"")
        report.append(f"📊 Strategy Breakdown:")
        
        for name, strategy_data in status['strategies'].items():
            report.append(f"")
            report.append(f"  {name.upper()}")
            report.append(f"    Weight:   {strategy_data['weight']*100:.1f}%")
            report.append(f"    Capital:  ${strategy_data['capital']:,.2f}")
            report.append(f"    PnL:      ${strategy_data['pnl']:+,.2f} ({strategy_data['pnl_pct']:+.2f}%)")
            report.append(f"    Trades:   {strategy_data['trades']}")
            report.append(f"    Status:   {'✅ Active' if strategy_data['active'] else '❌ Disabled'}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


if __name__ == '__main__':
    # Test portfolio manager
    from backend.agents.discovery.ranker from strategies import core as strategyMetrics
    from backend.agents.portfolio.strategy_selector from strategies import core as strategySelector
    
    # Create sample strategies
    strategies_list = [
        StrategyMetrics(
            strategy_name="Conservative",
            total_return_pct=25.0, cagr=12.0, sharpe_ratio=2.50,
            sortino_ratio=3.20, calmar_ratio=5.00,
            max_drawdown_pct=-5.0, avg_drawdown_pct=-2.5,
            volatility_annual_pct=8.0, total_trades=150,
            win_rate_pct=72.0, profit_factor=2.80,
            avg_win_pct=1.8, avg_loss_pct=-0.8,
            consecutive_wins=12, consecutive_losses=2,
            recovery_factor=5.0, composite_score=4.16
        ),
        StrategyMetrics(
            strategy_name="Balanced",
            total_return_pct=52.0, cagr=21.0, sharpe_ratio=2.15,
            sortino_ratio=2.85, calmar_ratio=4.00,
            max_drawdown_pct=-13.0, avg_drawdown_pct=-5.5,
            volatility_annual_pct=16.0, total_trades=180,
            win_rate_pct=65.0, profit_factor=2.40,
            avg_win_pct=2.8, avg_loss_pct=-1.4,
            consecutive_wins=9, consecutive_losses=4,
            recovery_factor=4.0, composite_score=3.21
        ),
        StrategyMetrics(
            strategy_name="Aggressive",
            total_return_pct=85.0, cagr=42.0, sharpe_ratio=1.20,
            sortino_ratio=1.50, calmar_ratio=2.50,
            max_drawdown_pct=-34.0, avg_drawdown_pct=-15.0,
            volatility_annual_pct=45.0, total_trades=220,
            win_rate_pct=55.0, profit_factor=1.95,
            avg_win_pct=5.2, avg_loss_pct=-3.8,
            consecutive_wins=7, consecutive_losses=8,
            recovery_factor=2.5, composite_score=1.71
        )
    ]
    
    # Select and categorize strategies
    selector = StrategySelector()
    selected = selector.select_top_n(strategies_list, n=3)
    categories = selector.categorize_strategies(selected)
    weights = selector.get_allocation_weights(categories, allocation_mode="balanced")
    
    # Create portfolio
    portfolio = MultiStrategyPortfolio(
        initial_capital=100000.0,
        allocation_mode="balanced"
    )
    
    # Setup strategies
    portfolio.setup_strategies(categories, weights)
    
    # Simulate some trades
    print(f"\n{'='*80}")
    print(f"SIMULATING TRADES")
    print(f"{'='*80}\n")
    
    portfolio.record_trade("conservative", 500, True)
    portfolio.record_trade("balanced", 1200, True)
    portfolio.record_trade("aggressive", 2500, True)
    portfolio.record_trade("conservative", 300, True)
    portfolio.record_trade("balanced", -800, False)
    portfolio.record_trade("aggressive", -1500, False)
    
    # Check rebalancing
    print(f"")
    needs_rebalance = portfolio.check_rebalancing_needed(threshold_pct=5.0)
    if needs_rebalance:
        portfolio.rebalance()
    
    # Print performance report
    print(f"\n{portfolio.get_performance_report()}")