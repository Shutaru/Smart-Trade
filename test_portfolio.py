"""
Test Portfolio Manager

Test script for multi-strategy portfolio management system.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.agents.discovery.ranker import StrategyMetrics
from backend.agents.portfolio.strategy_selector import StrategySelector
from backend.agents.portfolio.portfolio_manager import MultiStrategyPortfolio


def test_strategy_selector():
    """Test strategy selection"""
    
    print("="*80)
    print("TEST 1: Strategy Selector")
    print("="*80)
    
    # Create sample strategies
    strategies = [
        StrategyMetrics(
            strategy_name="Conservative",
            total_return_pct=25.0,
            cagr=12.0,
            sharpe_ratio=2.50,
            sortino_ratio=3.20,
            calmar_ratio=5.00,
            max_drawdown_pct=-5.0,
            avg_drawdown_pct=-2.5,
            volatility_annual_pct=8.0,
            total_trades=150,
            win_rate_pct=72.0,
            profit_factor=2.80,
            avg_win_pct=1.8,
            avg_loss_pct=-0.8,
            consecutive_wins=12,
            consecutive_losses=2,
            recovery_factor=5.0,
            composite_score=4.16
        ),
        StrategyMetrics(
            strategy_name="Balanced",
            total_return_pct=52.0,
            cagr=21.0,
            sharpe_ratio=2.15,
            sortino_ratio=2.85,
            calmar_ratio=4.00,
            max_drawdown_pct=-13.0,
            avg_drawdown_pct=-5.5,
            volatility_annual_pct=16.0,
            total_trades=180,
            win_rate_pct=65.0,
            profit_factor=2.40,
            avg_win_pct=2.8,
            avg_loss_pct=-1.4,
            consecutive_wins=9,
            consecutive_losses=4,
            recovery_factor=4.0,
            composite_score=3.21
        ),
        StrategyMetrics(
            strategy_name="Aggressive",
            total_return_pct=85.0,
            cagr=42.0,
            sharpe_ratio=1.20,
            sortino_ratio=1.50,
            calmar_ratio=2.50,
            max_drawdown_pct=-34.0,
            avg_drawdown_pct=-15.0,
            volatility_annual_pct=45.0,
            total_trades=220,
            win_rate_pct=55.0,
            profit_factor=1.95,
            avg_win_pct=5.2,
            avg_loss_pct=-3.8,
            consecutive_wins=7,
            consecutive_losses=8,
            recovery_factor=2.5,
            composite_score=1.71
        )
    ]
    
    selector = StrategySelector()
    
    # Select top 3
    selected = selector.select_top_n(strategies, n=3, min_score=1.0)
    
    print(f"\n✅ Selected {len(selected)} strategies:")
    for i, s in enumerate(selected, 1):
        print(f"  {i}. {s.strategy_name} (Score: {s.composite_score:.4f})")
    
    # Categorize
    categories = selector.categorize_strategies(selected)
    
    print(f"\n📊 Categorization:")
    for category, strategy in categories.items():
        if strategy:
            print(f"  {category.capitalize()}: {strategy.strategy_name}")
    
    # Get allocation weights
    weights = selector.get_allocation_weights(categories, allocation_mode="balanced")
    
    print(f"\n💰 Allocation (Balanced Mode):")
    for category, weight in weights.items():
        print(f"  {category.capitalize()}: {weight*100:.1f}%")
    
    # Calculate portfolio metrics
    portfolio_metrics = selector.calculate_portfolio_metrics(categories, weights)
    
    print(f"\n📈 Expected Portfolio Metrics:")
    print(f"  Return: {portfolio_metrics['expected_return']:.2f}%")
    print(f"  Sharpe: {portfolio_metrics['expected_sharpe']:.2f}")
    print(f"  Max DD: {portfolio_metrics['expected_max_dd']:.2f}%")
    print(f"  Volatility: {portfolio_metrics['expected_volatility']:.2f}%")
    print(f"  Win Rate: {portfolio_metrics['expected_win_rate']:.1f}%")
    
    print("\n✅ Strategy Selector test passed!")
    
    return categories, weights


def test_portfolio_manager(categories, weights):
    """Test portfolio manager"""
    
    print("\n" + "="*80)
    print("TEST 2: Portfolio Manager")
    print("="*80)
    
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
    portfolio.record_trade("conservative", 450, True)
    portfolio.record_trade("balanced", 980, True)
    portfolio.record_trade("aggressive", -600, False)
    
    # Check rebalancing
    print(f"")
    needs_rebalance = portfolio.check_rebalancing_needed(threshold_pct=5.0)
    if needs_rebalance:
        portfolio.rebalance()
    
    # Print performance report
    print(f"\n{portfolio.get_performance_report()}")
    
    print("\n✅ Portfolio Manager test passed!")
    
    return portfolio


if __name__ == '__main__':
    print("🤖 Multi-Strategy Portfolio Manager Test Suite")
    print("")
    
    # Test 1: Strategy Selector
    categories, weights = test_strategy_selector()
    
    # Test 2: Portfolio Manager
    portfolio = test_portfolio_manager(categories, weights)
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
    print("\n📊 Summary:")
    status = portfolio.get_portfolio_status()
    print(f"  Total Equity: ${status['current_equity']:,.2f}")
    print(f"  Total PnL: ${status['total_pnl']:+,.2f} ({status['total_pnl_pct']:+.2f}%)")
    print(f"  Win Rate: {status['win_rate']:.1f}%")
    print(f"  Total Trades: {status['total_trades']}")
    print("")
    print("✅ Multi-Strategy Portfolio System is ready!")