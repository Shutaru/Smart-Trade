"""
Test Strategy Discovery with Real Backtests

NEW: Multi-Symbol & Multi-Timeframe Support!

Usage:
    python discovery/run.py
    python discovery/run.py --symbol ETH/USDT --exchange binance --timeframe 1h
    python discovery/run.py --symbol BTC/USDT:USDT --exchange bitget --timeframe 5m --strategies 10
"""

import sys
import os
import asyncio
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.discovery.discovery_engine import StrategyDiscoveryEngine


async def main():
    """Main entry point for strategy discovery"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Strategy Discovery Engine - Multi-Symbol & Multi-Timeframe')
    parser.add_argument('--symbol', type=str, default=None, help='Trading symbol (e.g., BTC/USDT:USDT, ETH/USDT)')
    parser.add_argument('--exchange', type=str, default=None, help='Exchange name (binance, bitget, etc)')
    parser.add_argument('--timeframe', type=str, default=None, help='Candle timeframe (5m, 1h, 4h, etc)')
    parser.add_argument('--strategies', type=int, default=5, help='Number of strategies to test (default: 5)')
    parser.add_argument('--parallel', type=int, default=2, help='Max parallel backtests (default: 2)')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("="*80)
    print("STRATEGY DISCOVERY ENGINE - REAL BACKTEST MODE")
    print("="*80)
    print("")
    
    # Load config to get defaults
    if not os.path.exists(args.config):
        print(f"ERROR: {args.config} not found!")
        print(f"   Please create {args.config} from config.example.yaml")
        return
    
    import yaml
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
    
    # Determine final configuration (CLI args override config.yaml)
    symbol = args.symbol or config.get('symbol', 'BTC/USDT:USDT')
    exchange = args.exchange or config.get('exchange', 'binance')
    timeframe = args.timeframe or config.get('timeframe', '5m')

    print("Configuration:")
    print(f"  Symbol:     {symbol}")
    print(f"  Exchange:   {exchange}")
    print(f"  Timeframe:  {timeframe}")
    print(f"  Strategies: {args.strategies}")
    print(f"  Parallel:   {args.parallel}")
    print("")
    
    # Check database
    db_path = config.get("db", {}).get("path")
    if db_path:
        # Try to construct timeframe-specific DB path
        sym_safe = symbol.replace('/', '_').replace(':', '_')
        db_candidates = [
            db_path,
            f"data/db/{sym_safe}_{timeframe}.db",
            f"data/db/{sym_safe}_5m.db"  # Fallback to 5m
        ]
        
        db_exists = False
        for db in db_candidates:
            if os.path.exists(db):
                print(f"Database found: {db}")
                db_exists = True
                break
        
        if not db_exists:
            print(f"WARNING: No database found for {symbol} {timeframe}")
            print(f"  Searched: {db_candidates}")
            print(f"  The engine will attempt to download data automatically...")
            print("")
    
    print("="*80)
    print("READY TO START DISCOVERY")
    print("="*80)
    print("")
    print("This will:")
    print(f"  1. Test {args.strategies} strategy candidates")
    print(f"  2. Run real backtests on {symbol} ({exchange}, {timeframe})")
    print(f"  3. Rank strategies by performance")
    print(f"  4. Show top 3 strategies for portfolio allocation")
    print("")
    
    if not args.yes:
        response = input("Do you want to continue? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("Cancelled by user")
            return
    
    print("")
    print("="*80)
    print("STARTING DISCOVERY PROCESS")
    print("="*80)
    print("")
    
    # Initialize discovery engine with parameters
    engine = StrategyDiscoveryEngine(
        config_path=args.config,
        symbol=symbol,
        exchange=exchange,
        timeframe=timeframe,
        max_parallel=args.parallel
    )
    
    # Run discovery
    try:
        strategies = await engine.discover_strategies(num_strategies=args.strategies)
        
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
        print(f"TOP 3 STRATEGIES FOR {symbol} ({timeframe})")
        print("="*80)
        print("")
        
        for i, strategy in enumerate(top3, 1):
            print(f"#{i} {strategy.strategy_name}")
            print(f"   Composite Score: {strategy.composite_score:.4f}")
            print(f"   Return:       {strategy.total_return_pct:+.2f}%")
            print(f"   Max DD:          {strategy.max_drawdown_pct:.2f}%")
            print(f" Sharpe:       {strategy.sharpe_ratio:.2f}")
            print(f"   Win Rate:        {strategy.win_rate_pct:.1f}%")
            print(f"   Total Trades:    {strategy.total_trades}")
            print("")
        
        print("="*80)
        print("DISCOVERY COMPLETE")
        print("="*80)
        print("")
        print("Next steps:")
        print(f"1. Review the top 3 strategies above for {symbol}")
        print("2. Run optimization on best strategy:")
        print(f"   python optimization/optimizer.py --strategy {top3[0].strategy_name}")
        print("3. Or create portfolio with multiple strategies")
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
    asyncio.run(main())