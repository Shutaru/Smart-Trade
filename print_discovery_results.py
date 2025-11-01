"""
Print Discovery Results - 38 Strategies Summary

Displays results from the last discovery run without JSON serialization issues.
"""

import os
import glob
import json


def print_summary():
    """Print summary of last discovery run"""
    
    # Try to find the most recent backtest results
    backtest_dirs = glob.glob("data/backtests/*")
    if not backtest_dirs:
        print("No backtest results found")
        return
    
    # Get most recent 38 directories (from last run)
    backtest_dirs.sort(reverse=True)
    recent_dirs = backtest_dirs[:38]
    
    print("\n" + "="*100)
    print("📊 38 STRATEGIES - 5MIN TIMEFRAME RESULTS")
    print("="*100)
    
    results = []
    
    for dir_path in recent_dirs:
        summary_file = os.path.join(dir_path, "summary.json")
        if os.path.exists(summary_file):
            with open(summary_file, 'r') as f:
                data = json.load(f)
                results.append({
                    'dir': os.path.basename(dir_path),
                    'trades': data.get('trades', 0),
                    'win_rate': data.get('win_rate_pct', 0),
                    'return': data.get('ret_tot_pct', 0),
                    'sharpe': data.get('sharpe_ann', 0),
                    'max_dd': data.get('maxdd_pct', 0),
                    'profit_factor': data.get('profit_factor', 0)
                })
    
    # Sort by return
    results.sort(key=lambda x: x['return'], reverse=True)
    
    # Count profitable
    profitable = [r for r in results if r['return'] > 0]
    
    print(f"\n✅ SUCCESS RATE: {len(profitable)}/{len(results)} profitable ({len(profitable)/len(results)*100:.1f}%)")
    print(f"\n🏆 TOP 10 STRATEGIES:")
    print("-" * 100)
    
    for i, r in enumerate(results[:10], 1):
        status = "✓" if r['return'] > 0 else "✗"
        print(f"{i:2d}. {status} Return: {r['return']:+7.2f}% | Sharpe: {r['sharpe']:6.2f} | Win Rate: {r['win_rate']:5.1f}% | Trades: {r['trades']:4d} | DD: {r['max_dd']:6.2f}%")
    
    print("\n" + "="*100)
    
    if profitable:
        avg_return = sum(r['return'] for r in profitable) / len(profitable)
        avg_sharpe = sum(r['sharpe'] for r in profitable) / len(profitable)
        avg_trades = sum(r['trades'] for r in profitable) / len(profitable)
        
        print(f"\n📈 PROFITABLE STRATEGIES AVERAGES:")
        print(f"   Average Return: {avg_return:.2f}%")
        print(f"   Average Sharpe: {avg_sharpe:.2f}")
        print(f"   Average Trades: {avg_trades:.0f}")
    
    print("\n" + "="*100 + "\n")


if __name__ == '__main__':
    print_summary()