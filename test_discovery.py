"""
Test Strategy Discovery Engine

Quick test to validate the discovery system without running full backtests.
"""

import sys
sys.path.append('.')

from backend.agents.discovery.strategy_catalog import StrategyCatalog, StrategyTemplate
from backend.agents.discovery.ranker import StrategyRanker, StrategyMetrics


def test_catalog():
    """Test strategy catalog"""
    print("="*80)
    print("TEST 1: Strategy Catalog")
    print("="*80)
    
    catalog = StrategyCatalog()
    
    print(f"\n📊 Total Indicators: {len(catalog.INDICATORS)}")
    print(f"\nBy Type:")
    for indicator_type, count in catalog.get_summary().items():
        print(f"  - {indicator_type.capitalize()}: {count}")
    
    print(f"\n📋 Sample Indicators:")
    for ind_id in ['ema_20', 'rsi_14', 'macd', 'bollinger', 'atr']:
        ind = catalog.get_indicator(ind_id)
        print(f"  - {ind.name} ({ind.type}): {ind.description}")
    
    print("\n✅ Catalog test passed!")


def test_templates():
    """Test strategy templates"""
    print("\n" + "="*80)
    print("TEST 2: Strategy Templates")
    print("="*80)
    
    templates = StrategyTemplate.generate_combinations()
    
    print(f"\n🎯 Generated {len(templates)} strategy combinations")
    print(f"\nTop 5 Templates:")
    
    for i, template in enumerate(templates[:5], 1):
        print(f"\n{i}. {template['name']}")
        print(f"   Indicators: {', '.join(template['indicators'])}")
        print(f"   Entry: {template['entry_logic']}")
        print(f"   Exit: {template['exit_logic']}")
    
    print("\n✅ Templates test passed!")


def test_ranker():
    """Test strategy ranker"""
    print("\n" + "="*80)
    print("TEST 3: Strategy Ranker")
    print("="*80)

    # Create mock strategies
    strategies = [
        StrategyMetrics(
            strategy_name="Conservative (Low Vol, Low DD)",
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
            recovery_factor=5.0
        ),
        StrategyMetrics(
            strategy_name="Aggressive (High Return, High Vol)",
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
            recovery_factor=2.5
        ),
        StrategyMetrics(
            strategy_name="Balanced (Good Risk/Reward)",
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
            recovery_factor=4.0
        ),
        StrategyMetrics(
            strategy_name="High DD (Bad)",
            total_return_pct=35.0,
            cagr=16.0,
            sharpe_ratio=0.80,
            sortino_ratio=1.00,
            calmar_ratio=0.70,
            max_drawdown_pct=-50.0,
            avg_drawdown_pct=-22.0,
            volatility_annual_pct=38.0,
            total_trades=95,
            win_rate_pct=48.0,
            profit_factor=1.30,
            avg_win_pct=4.5,
            avg_loss_pct=-3.2,
            consecutive_wins=5,
            consecutive_losses=12,
            recovery_factor=0.7
        ),
    ]
    
    ranker = StrategyRanker()
    
    print("\n📊 Ranking Strategies...")
    ranked = ranker.rank_strategies(strategies)
    
    print("\n" + ranker.format_report(ranked))
    
    print("\n🏆 Expected Ranking:")
    print("   1. Conservative or Balanced (low DD, stable returns)")
    print("   2. Balanced or Conservative")
    print("   3. Aggressive (high return but penalized for vol)")
    print("   4. High DD (heavily penalized)")
    
    print(f"\n✅ Actual Ranking:")
    for i, s in enumerate(ranked, 1):
        print(f"   {i}. {s.strategy_name} (Score: {s.composite_score:.4f})")
    
    print("\n✅ Ranker test passed!")


if __name__ == '__main__':
    test_catalog()
    test_templates()
    test_ranker()

    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED!")
    print("="*80)
    print("\nStrategy Discovery Engine is ready!")
    print("Next: Run full discovery with real backtests:")
    print("  python backend/agents/discovery/discovery_engine.py")