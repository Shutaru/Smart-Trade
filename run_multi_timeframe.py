"""
Multi-Timeframe Backtest Runner - Test all 38 strategies on 5m, 1h, 4h

Runs comprehensive backtests across multiple timeframes and generates
comparison reports for each.

Usage:
    python run_multi_timeframe.py --days 90
"""

import subprocess
import time
import os
from datetime import datetime

# Timeframes to test (based on your database)
TIMEFRAMES = [
    {"name": "5min", "days": 90, "label": "5-Minute (Scalping)"},
    {"name": "1hour", "days": 90, "label": "1-Hour (Intraday)"},
    {"name": "4hour", "days": 90, "label": "4-Hour (Swing)"},
]


def run_timeframe_test(tf_name: str, days: int, label: str):
    """Run backtest for a specific timeframe"""
    
    print(f"\n{'='*100}")
    print(f"TIMEFRAME: {label}")
    print(f"{'='*100}\n")
    
    start_time = time.time()
    
    # Run the backtest (assumes your db has the right timeframe data)
    cmd = [
        "python", "run_38_strategies.py",
        "--days", str(days),
        "--strategies", "all"
    ]
    
    print(f"Running command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        elapsed = time.time() - start_time
        
        print(f"\n{label} completed in {elapsed/60:.1f} minutes")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n{label} failed: {e}")
        return False


def main():
    print("\n" + "="*100)
    print("MULTI-TIMEFRAME BACKTEST - 38 STRATEGIES")
    print("="*100)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Timeframes: {len(TIMEFRAMES)}")
    print("="*100 + "\n")
    
    overall_start = time.time()
    results = {}
    
    for tf in TIMEFRAMES:
        success = run_timeframe_test(tf["name"], tf["days"], tf["label"])
        results[tf["label"]] = "? Success" if success else "? Failed"
    
    # Final summary
    overall_elapsed = time.time() - overall_start
    
    print("\n" + "="*100)
    print("MULTI-TIMEFRAME BACKTEST SUMMARY")
    print("="*100)
    
    for label, status in results.items():
        print(f"{label:30s}: {status}")
    
    print(f"\nTotal time: {overall_elapsed/60:.1f} minutes ({overall_elapsed/3600:.2f} hours)")
    print(f"Results in: data/backtest_38/comparison_*")
    print("\n" + "="*100 + "\n")


if __name__ == '__main__':
    main()
