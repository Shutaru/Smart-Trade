"""
Strategy Discovery - 5min vs 1h vs 4h Comparison Script

Runs 38 strategies on multiple timeframes and compares results.
"""

import asyncio
import json
import time
import os
from datetime import datetime
from backend.agents.discovery.discovery_engine from strategies import core as strategyDiscoveryEngine


async def run_discovery_timeframe(timeframe: str, num_strategies: int = 38):
    """Run discovery on a specific timeframe"""
    print("\n" + "="*100)
    print(f"RUNNING DISCOVERY: {num_strategies} strategies on {timeframe} timeframe")
    print("="*100)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Estimated duration: ~30-35 minutes")
    print("="*100 + "\n")
    
    start_time = time.time()
    
    # Initialize engine with timeframe override
    engine = StrategyDiscoveryEngine(
        config_path='config.yaml',
        max_parallel=1,
        timeframe=timeframe  # Override config.yaml timeframe
    )
    
    # Run discovery
    results = await engine.discover_strategies(num_strategies=num_strategies)
    
    elapsed = time.time() - start_time
    
    # Save results
    output_dir = os.path.join("data", "discovery_comparison")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = int(time.time())
    output_file = os.path.join(output_dir, f"results_{timeframe}_{timestamp}.txt")
    
    # Save as text (avoid JSON serialization issues)
    with open(output_file, 'w') as f:
        f.write(f"Timeframe: {timeframe}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Strategies tested: {num_strategies}\n")
        f.write(f"Elapsed seconds: {elapsed}\n")
        f.write(f"\n{'-'*80}\n\n")
        f.write(str(results))
    
    print("\n" + "="*100)
    print(f"✓ {timeframe} DISCOVERY COMPLETE")
    print(f"Total time: {elapsed/60:.1f} minutes ({elapsed:.0f} seconds)")
    print(f"Results saved to: {output_file}")
    print("="*100 + "\n")
    
    return results, output_file, elapsed


def print_comparison_summary(results_5min, results_1h, results_4h):
    """Print side-by-side comparison of all timeframes"""
    print("\n" + "="*100)
    print("📊 TIMEFRAME COMPARISON SUMMARY")
    print("="*100 + "\n")
    
    timeframes = [
        ('5min', results_5min),
        ('1h', results_1h),
        ('4h', results_4h)
    ]
    
    print(f"{'Metric':<30} {'5min':>15} {'1h':>15} {'4h':>15}")
    print("-" * 100)
    
    # Extract metrics from each timeframe
    for tf_name, results in timeframes:
        if results and 'strategies' in results:
            strategies = results['strategies']
            profitable = [s for s in strategies if s.get('metrics', {}).get('total_return', 0) > 0]
            
            if tf_name == '5min':
                print(f"{'Total Strategies':<30} {len(strategies):>15d}")
            
            if tf_name == '5min':
                print(f"{'Profitable':<30} {len(profitable):>15d}", end='')
            elif tf_name == '1h':
                print(f" {len(profitable):>15d}", end='')
            else:
                print(f" {len(profitable):>15d}")
    
    print("\n" + "="*100)
    
    # Print top 3 for each timeframe
    for tf_name, results in timeframes:
        if results and 'strategies' in results:
            print(f"\n🏆 TOP 3 - {tf_name.upper()}")
            print("-" * 100)
            
            strategies = results['strategies']
            sorted_strategies = sorted(strategies, key=lambda x: x.get('composite_score', 0), reverse=True)[:3]
            
            for i, strat in enumerate(sorted_strategies, 1):
                metrics = strat.get('metrics', {})
                name = strat.get('name', 'Unknown')
                ret = metrics.get('total_return', 0)
                sharpe = metrics.get('sharpe', 0)
                trades = metrics.get('total_trades', 0)
                
                print(f"{i}. {name:<30} Return: {ret:+7.2f}% | Sharpe: {sharpe:6.2f} | Trades: {trades:5d}")
    
    print("\n" + "="*100 + "\n")


async def main():
    """Main execution - run all 3 timeframes sequentially"""
    total_start = time.time()
    
    print("\n" + "="*100)
    print("🚀 STRATEGY DISCOVERY COMPARISON: 5min vs 1h vs 4h")
    print("="*100)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total strategies per timeframe: 38")
    print(f"Estimated total time: ~90-110 minutes (3 timeframes × ~35 min)")
    print("="*100 + "\n")
    
    results = {}
    
    # Phase 1: Run 5min
    print("\n" + "🔹 PHASE 1/3: 5min Timeframe")
    results['5min'], file_5min, elapsed_5min = await run_discovery_timeframe('5m', 38)
    
    # Phase 2: Run 1h
    print("\n" + "🔹 PHASE 2/3: 1h Timeframe")
    results['1h'], file_1h, elapsed_1h = await run_discovery_timeframe('1h', 38)
    
    # Phase 3: Run 4h
    print("\n" + "🔹 PHASE 3/3: 4h Timeframe")
    results['4h'], file_4h, elapsed_4h = await run_discovery_timeframe('4h', 38)
    
    total_elapsed = time.time() - total_start
    
    print("\n" + "="*100)
    print(f"✓ DISCOVERY COMPARISON COMPLETE")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print("="*100 + "\n")
    
    # Print summary
    print("📊 RESULTS SUMMARY:\n")
    
    for tf_name in ['5min', '1h', '4h']:
        result = results.get(tf_name)
        if result:
            strategies = result if isinstance(result, list) else []
            profitable = [s for s in strategies if s.total_return_pct > 0]
            
            print(f"✅ {tf_name.upper()}:")
            print(f"   - Total strategies: {len(strategies)}")
            print(f"   - Profitable: {len(profitable)}")
            if profitable:
                best = max(profitable, key=lambda s: s.composite_score)
                print(f"   - Best: {best.strategy_name}")
                print(f"  Return: {best.total_return_pct:+.2f}% | Sharpe: {best.sharpe_ratio:.2f} | Score: {best.composite_score:.2f}")
        else:
            print(f"❌ {tf_name.upper()}: Failed")
        print()
    
    print("="*100)
    print("💡 Next steps:")
    print("   1. Review results for each timeframe")
    print("   2. Choose best timeframe based on:")
    print("  - Most profitable strategies")
    print("      - Best risk-adjusted returns (Sharpe)")
    print("      - Lowest drawdowns")
    print("   3. Optimize top strategies on chosen timeframe")
    print("="*100 + "\n")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Discovery cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error during discovery: {e}")
        raise