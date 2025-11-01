"""
Complete Validation Pipeline - Baseline vs Optimized
"""

import sys
import json
import subprocess
import time
import argparse
import yaml
from pathlib import Path
from datetime import datetime
import pandas as pd

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_header(title):
    print(f"\n{'='*80}\n{title}\n{'='*80}\n")


def run_command(cmd, description):
    print(f"[Running] {description}...")
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"[OK] {description} completed in {elapsed:.1f}s\n")
        return True, result.stdout, elapsed
    else:
        print(f"[FAIL] {description}\n")
        return False, result.stderr, elapsed


def parse_json_output(output):
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('{'):
            try:
                return json.loads(line)
            except:
                continue
    return None


def main():
    parser = argparse.ArgumentParser(description='Validation Pipeline')
    parser.add_argument('--symbol', default='BTC/USDT:USDT')
    parser.add_argument('--exchange', default='binance')
    parser.add_argument('--timeframe', default='5m')
    parser.add_argument('--days', type=int, default=1460)
    parser.add_argument('--trials', type=int, default=50)
    args = parser.parse_args()
    
    strategies = ['bollinger_mean_reversion', 'cci_extreme_snapback', 'vwap_institutional_trend']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('data/validation') / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print_header("VALIDATION PIPELINE")
    print(f"Symbol: {args.symbol} | Period: {args.days} days | Trials: {args.trials}")
    print(f"Output: {output_dir}\n")
    
    results = {'baseline': {}, 'optimization': {}, 'post_optimization': {}}
    
    # STEP 1: Baseline
    print_header(f"STEP 1: BASELINE ({args.days} days)")
    for strategy in strategies:
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
        cfg.update({'strategy': strategy, 'symbol': args.symbol, 'exchange': args.exchange, 'timeframe': args.timeframe})
        with open('config.yaml', 'w') as f:
            yaml.safe_dump(cfg, f)
        
        cmd = [sys.executable, 'optimization/backtest_engine.py', '--days', str(args.days)]
        success, output, elapsed = run_command(cmd, f"Baseline: {strategy}")
        
        metrics = parse_json_output(output) if success else None
        if metrics and 'error' not in metrics:
            results['baseline'][strategy] = {'metrics': metrics, 'elapsed': elapsed}
            print(f"  Return: {metrics['ret_tot_pct']:.2f}% | Sharpe: {metrics['sharpe_ann']:.2f} | Trades: {metrics['trades']}\n")
        else:
            results['baseline'][strategy] = {'error': 'Failed'}
    
    # STEP 2: Optimization
    print_header(f"STEP 2: OPTIMIZATION ({args.trials} trials)")
    for strategy in strategies:
        print(f"Optimizing: {strategy}\n")
        cmd = [sys.executable, 'run_optimizer.py', '--strategy', strategy, '--symbol', args.symbol,
               '--exchange', args.exchange, '--timeframe', args.timeframe, '--trials', str(args.trials), '--days', str(args.days)]
        success, output, elapsed = run_command(cmd, f"Optimize: {strategy}")
        
        opt_results = None
        if success:
            try:
                opt_dirs = list(Path('data/optimization').glob(f'opt_{strategy}_*'))
                if opt_dirs:
                    latest = max(opt_dirs, key=lambda p: p.stat().st_mtime)
                    with open(latest / 'optimization_results.json', 'r') as f:
                        opt_results = json.load(f)
            except:
                pass
        
        results['optimization'][strategy] = {'results': opt_results, 'elapsed': elapsed}
        if opt_results:
            print(f"  Best Score: {opt_results.get('best_value', 'N/A')}\n")
    
    # STEP 3: Post-optimization
    print_header("STEP 3: POST-OPTIMIZATION")
    for strategy in strategies:
        opt_data = results['optimization'].get(strategy, {}).get('results')
        if not opt_data or 'best_params' not in opt_data:
            print(f"  Skipping {strategy}: No params\n")
            continue
        
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
        cfg.update({'strategy': strategy, 'symbol': args.symbol, 'exchange': args.exchange, 'timeframe': args.timeframe})
        if 'risk' not in cfg:
            cfg['risk'] = {}
        cfg['risk'].update(opt_data['best_params'])
        with open('config.yaml', 'w') as f:
            yaml.safe_dump(cfg, f)
        
        cmd = [sys.executable, 'optimization/backtest_engine.py', '--days', str(args.days)]
        success, output, elapsed = run_command(cmd, f"Post-opt: {strategy}")
        
        metrics = parse_json_output(output) if success else None
        if metrics and 'error' not in metrics:
            results['post_optimization'][strategy] = {'metrics': metrics, 'elapsed': elapsed}
            print(f"  Return: {metrics['ret_tot_pct']:.2f}% | Sharpe: {metrics['sharpe_ann']:.2f} | Trades: {metrics['trades']}\n")
        else:
            results['post_optimization'][strategy] = {'error': 'Failed'}
    
    # Save results
    with open(output_dir / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # STEP 4: Comparison
    print_header("COMPARISON")
    comparison = []
    for strategy in strategies:
        baseline = results['baseline'].get(strategy, {}).get('metrics', {})
        post_opt = results['post_optimization'].get(strategy, {}).get('metrics', {})
        
        if baseline and post_opt:
            comparison.append({
                'Strategy': strategy,
                'Baseline Return': baseline.get('ret_tot_pct', 0),
                'Optimized Return': post_opt.get('ret_tot_pct', 0),
                'Improvement': post_opt.get('ret_tot_pct', 0) - baseline.get('ret_tot_pct', 0),
                'Baseline Sharpe': baseline.get('sharpe_ann', 0),
                'Optimized Sharpe': post_opt.get('sharpe_ann', 0)
            })
    
    if comparison:
        df = pd.DataFrame(comparison)
        for _, row in df.iterrows():
            print(f"\n{row['Strategy']}")
            print(f"  Return:  {row['Baseline Return']:>7.2f}% → {row['Optimized Return']:>7.2f}% (Δ {row['Improvement']:>+6.2f}%)")
            print(f"  Sharpe:  {row['Baseline Sharpe']:>7.2f}  → {row['Optimized Sharpe']:>7.2f}")
        
        df.to_csv(output_dir / 'comparison.csv', index=False)
        print(f"\n\nAverage improvement: {df['Improvement'].mean():+.2f}%")
        print(f"Results saved to: {output_dir}\n")


if __name__ == '__main__':
    main()