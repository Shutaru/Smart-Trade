"""
Test Strategy Discovery with Real Backtests

This script runs the complete strategy discovery pipeline:
1. Generate strategy candidates
2. Run backtests in parallel
3. Rank strategies by composite score
4. Display top 3 strategies for portfolio allocation
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.agents.discovery.discovery_engine from strategies import core as strategyDiscoveryEngine


async def main():
    """Main entry point for strategy discovery"""
    
    print("="*80)
    print("STRATEGY DISCOVERY ENGINE - REAL BACKTEST MODE")
    print("="*80)
    print("")
    print("WARNING: This will run real backtests on your data.")
    print("    Make sure you have:")
    print("    - config.yaml properly configured")
    print("    - Database with candle data (data/db/*.db)")
    print("    - At least 365 days of historical data")
    print("")
    
    # Check if config exists
    if not os.path.exists("config.yaml"):
        print("ERROR: config.yaml not found!")
        print("   Please create config.yaml from config.example.yaml")
        return
    
    # Check if database exists
    import yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    db_path = config.get("db", {}).get("path")
    if not db_path or not os.path.exists(db_path):
        print("ERROR: Database not found!")
        print(f"   Expected: {db_path}")
        print("   Please run bitget_backfill.py first or use the Data Management UI")
        return
    
    print(f"Config loaded: {config.get('symbol', 'Unknown')}")
    print(f"Database found: {db_path}")
    print("")
    
    # Ask for confirmation
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    if response not in ["yes", "y"]:
        print("Cancelled by user")
        return
    
    print("")
    print("="*80)
    print("STARTING DISCOVERY PROCESS")
    print("="*80)
    print("")
    
    # Initialize discovery engine
    engine = StrategyDiscoveryEngine(
        config_path="config.yaml",
        max_parallel=2  # Reduced to 2 for stability
    )
    
    # Run discovery (this will take several minutes)
    try:
        strategies = await engine.discover_strategies(num_strategies=5)  # Start with 5 strategies
        
        if len(strategies) == 0:
            print("")
            print("="*80)
            print("NO STRATEGIES PASSED VALIDATION")
            print("="*80)
            print("")
            print("Possible reasons:")
            print("- Backtests failed to run")
            print("- Not enough trades (< 10)")
            print("- Unacceptable drawdown (> 50%)")
            print("")
            return
        
        # Get top 3
        top3 = engine.ranker.get_top_n(strategies, n=3)
        
        print("")
        print("="*80)
        print("TOP 3 STRATEGIES FOR PORTFOLIO ALLOCATION")
        print("="*80)
        print("")
        
        for i, strategy in enumerate(top3, 1):
            print(f"#{i} {strategy.strategy_name}")
            print(f"   Composite Score: {strategy.composite_score:.4f}")
            print(f"   Return:          {strategy.total_return_pct:+.2f}%")
            print(f"   Max DD:          {strategy.max_drawdown_pct:.2f}%")
            print(f"   Sharpe:          {strategy.sharpe_ratio:.2f}")
            print(f"   Win Rate:        {strategy.win_rate_pct:.1f}%")
            print(f"   Total Trades:    {strategy.total_trades}")
            print("")
        
        print("="*80)
        print("DISCOVERY COMPLETE")
        print("="*80)
        print("")
        print("Next steps:")
        print("1. Review the top 3 strategies above")
        print("2. Run: python test_portfolio_live.py")
        print("   (This will create a portfolio with these strategies)")
        print("3. Start Agent Runner in the UI to begin live trading")
        print("")
        
    except KeyboardInterrupt:
        print("")
        print("Discovery cancelled by user (Ctrl+C)")
        print("")
    except Exception as e:
        print("")
        print("="*80)
        print("ERROR DURING DISCOVERY")
        print("="*80)
        print(f"Error: {e}")
        print("")
        import traceback
        traceback.print_exc()
        print("")


if __name__ == '__main__':
    # Run async main
    asyncio.run(main())