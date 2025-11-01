"""
Quick Discovery Runner - 38 Strategies on 5min

Run this to test all 38 professional strategies on 5min timeframe.
Results will be saved to data/discovery_results/
"""

import asyncio
import json
import time
import os
from datetime import datetime
from backend.agents.discovery.discovery_engine import StrategyDiscoveryEngine


async def main():
    print("\n" + "="*100)
    print("STRATEGY DISCOVERY - 38 PROFESSIONAL STRATEGIES (5min timeframe)")
    print("="*100)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Estimated duration: ~30-35 minutes")
    print("="*100 + "\n")
    
    start_time = time.time()
    
    # Initialize engine
    engine = StrategyDiscoveryEngine(config_path='config.yaml', max_parallel=1)
    
    # Run discovery
    results = await engine.discover_strategies(num_strategies=38)
    
    # Calculate elapsed time
    elapsed = time.time() - start_time
    
    # Save results with timestamp
    output_dir = os.path.join("data", "discovery_results")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = int(time.time())
    output_file = os.path.join(output_dir, f"38_strategies_5min_{timestamp}.json")
    
    # Save full results
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'timeframe': '5min',
            'num_strategies': 38,
            'elapsed_seconds': elapsed,
            'results': results
        }, f, indent=2)
    
    print("\n" + "="*100)
    print(f"✓ DISCOVERY COMPLETE")
    print(f"Total time: {elapsed/60:.1f} minutes ({elapsed:.0f} seconds)")
    print(f"Results saved to: {output_file}")
    print("="*100 + "\n")
    
    # Print quick summary
    if results and 'strategies' in results:
        profitable = [s for s in results['strategies'] if s.get('metrics', {}).get('total_return', 0) > 0]
        print(f"📊 Quick Summary:")
        print(f"   - Total strategies tested: {len(results['strategies'])}")
        print(f"   - Profitable strategies: {len(profitable)}")
        print(f"   - Success rate: {len(profitable)/len(results['strategies'])*100:.1f}%")
        
        if profitable:
            print(f"\n🏆 Top 3 Profitable:")
            sorted_profitable = sorted(profitable, key=lambda x: x.get('composite_score', 0), reverse=True)[:3]
            for i, strat in enumerate(sorted_profitable, 1):
                metrics = strat.get('metrics', {})
                print(f"   {i}. {strat.get('name')}")
                print(f"      Return: {metrics.get('total_return', 0):.2f}% | Sharpe: {metrics.get('sharpe', 0):.2f} | Trades: {metrics.get('total_trades', 0)}")
        print()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Discovery cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error during discovery: {e}")
        raise