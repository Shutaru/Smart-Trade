"""
Complete Validation Pipeline

Runs full validation workflow:
1. Baseline backtest (4 years, TOP 3 strategies)
2. Optimization (50 trials each)
3. Post-optimization backtest
4. Comparison report
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
    print(f"[Command] {' '.join(cmd)}\n")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"[OK] {description} completed in {elapsed:.1f}s\n")
        return True, result.stdout, elapsed
    else:
        print(f"[FAIL] {description} failed!\nError: {result.stderr}\n")
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
    parser = argparse.ArgumentParser(description='Complete Validation Pipeline')
    parser.add_argument('--symbol', default='BTC/USDT:USDT')
    parser.add_argument('--exchange', default='binance')
    parser.add_argument('--timeframe', default='5m')
    parser.add_argument('--days', type=int, default=1460)
    parser.add_argument('--trials', type=int, default=50)
    args = parser.parse_args()
    
    strategies = ['bollinger_mean_reversion', 'cci_extreme_snapback', 'vwap_institutional_trend']
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('data') / 'validation' / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print_header("COMPLETE VALIDATION PIPELINE")
    print(f"Timestamp: {timestamp}")
    print(f"Symbol: {args.symbol} | Exchange: {args.exchange} | Timeframe: {args.timeframe}")
    print(f"Period: {args.days} days (~{args.days/365:.1f} years)")
    print(f"Strategies: {', '.join(strategies)}")
    print(f"Optimization trials: {args.trials} per strategy")
    print(f"Output: {output_dir}\n")
    
    results = {
        'config': {'timestamp': timestamp, 'symbol': args.symbol, 'exchange': args.exchange,
                   'timeframe': args.timeframe, 'days': args.days, 'trials': args.trials, 'strategies': strategies},
        'baseline': {}, 'optimization': {}, 'post_optimization': {}
    }
    
    # ========================================================================
    # STEP 1: BASELINE BACKTEST
    # ========================================================================
    print_header(f"STEP 1: BASELINE BACKTEST ({args.days} days)")
    
    baseline_results = {}
    for strategy in strategies:
        # Update config
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
        cfg.update({'strategy': strategy, 'symbol': args.symbol, 'exchange': args.exchange, 'timeframe': args.timeframe})
        with open('config.yaml', 'w') as f:
            yaml.safe_dump(cfg, f)
        
        # Run backtest
        cmd = [sys.executable, 'optimization/backtest_engine.py', '--days', str(args.days)]
        success, output, elapsed = run_command(cmd, f"Baseline: {strategy}")
        
        if success:
            metrics = parse_json_output(output)
            if metrics and 'error' not in metrics:
                baseline_results[strategy] = {'metrics': metrics, 'elapsed': elapsed}
                print(f"  Return: {metrics['ret_tot_pct']:.2f}% | Sharpe: {metrics['sharpe_ann']:.2f} | Trades: {metrics['trades']}\n")
            else:
                baseline_results[strategy] = {'error': metrics.get('error', 'Unknown')}
        else:
            baseline_results[strategy] = {'error': output}
    
    results['baseline'] = baseline_results
    with open(output_dir / 'results_step1_baseline.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # ========================================================================
    # STEP 2: OPTIMIZATION
    # ========================================================================
    print_header(f"STEP 2: OPTIMIZATION ({args.trials} trials per strategy)")
    
    optimization_results = {}
    for strategy in strategies:
        print(f"\n{'-'*80}\nOptimizing: {strategy}\n{'-'*80}\n")
        
        cmd = [sys.executable, 'run_optimizer.py', '--strategy', strategy, '--symbol', args.symbol,
               '--exchange', args.exchange, '--timeframe', args.timeframe, '--trials', str(args.trials), '--days', str(args.days)]
        success, output, elapsed = run_command(cmd, f"Optimize: {strategy}")
        
        if success:
            opt_results = None
            try:
                opt_dirs = list(Path('data/optimization').glob(f'opt_{strategy}_*'))
                if opt_dirs:
                    latest_opt = max(opt_dirs, key=lambda p: p.stat().st_mtime)
                    results_file = latest_opt / 'optimization_results.json'
                    if results_file.exists():
                        with open(results_file, 'r') as f:
                            opt_results = json.load(f)
            except Exception as e:
                print(f"  Warning: Could not load optimization results: {e}")
            
            optimization_results[strategy] = {'results': opt_results, 'elapsed': elapsed}
            if opt_results:
                print(f"  Best Score: {opt_results.get('best_value', 'N/A')}\n")
        else:
            optimization_results[strategy] = {'error': output}
    
    results['optimization'] = optimization_results
    with open(output_dir / 'results_step2_optimization.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # ========================================================================
    # STEP 3: POST-OPTIMIZATION BACKTEST
    # ========================================================================
    print_header("STEP 3: POST-OPTIMIZATION BACKTEST")
    
    post_opt_results = {}
    for strategy in strategies:
        opt_data = optimization_results.get(strategy, {}).get('results')
        if not opt_data or 'best_params' not in opt_data:
            print(f"  Skipping {strategy}: No optimized parameters\n")
            continue
        
        # Update config with optimized parameters
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
        cfg.update({'strategy': strategy, 'symbol': args.symbol, 'exchange': args.exchange, 'timeframe': args.timeframe})
        if 'risk' not in cfg:
            cfg['risk'] = {}
        cfg['risk'].update(opt_data['best_params'])
        with open('config.yaml', 'w') as f:
            yaml.safe_dump(cfg, f)
        
        # Run backtest
        cmd = [sys.executable, 'optimization/backtest_engine.py', '--days', str(args.days)]
        success, output, elapsed = run_command(cmd, f"Post-opt: {strategy}")
        
        if success:
            metrics = parse_json_output(output)
            if metrics and 'error' not in metrics:
                post_opt_results[strategy] = {'metrics': metrics, 'elapsed': elapsed, 'optimized_params': opt_data['best_params']}
                print(f"  Return: {metrics['ret_tot_pct']:.2f}% | Sharpe: {metrics['sharpe_ann']:.2f} | Trades: {metrics['trades']}\n")
            else:
                post_opt_results[strategy] = {'error': metrics.get('error', 'Unknown')}
        else:
            post_opt_results[strategy] = {'error': output}
    
    results['post_optimization'] = post_opt_results
    with open(output_dir / 'validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # ========================================================================
    # STEP 4: COMPARISON REPORT
    # ========================================================================
    print_header("STEP 4: COMPARISON REPORT")
    
    comparison = []
    for strategy in strategies:
        baseline = baseline_results.get(strategy, {}).get('metrics', {})
        post_opt = post_opt_results.get(strategy, {}).get('metrics', {})
        
        if baseline and post_opt:
            row = {
                'Strategy': strategy,
                'Baseline Return %': baseline.get('ret_tot_pct', 0),
                'Optimized Return %': post_opt.get('ret_tot_pct', 0),
                'Improvement %': post_opt.get('ret_tot_pct', 0) - baseline.get('ret_tot_pct', 0),
                'Baseline Sharpe': baseline.get('sharpe_ann', 0),
                'Optimized Sharpe': post_opt.get('sharpe_ann', 0),
                'Baseline Trades': baseline.get('trades', 0),
                'Optimized Trades': post_opt.get('trades', 0)
            }
            comparison.append(row)
    
    if comparison:
        df = pd.DataFrame(comparison)
        print("\n" + "="*100 + "\nBEFORE vs AFTER OPTIMIZATION\n" + "="*100 + "\n")
        for _, row in df.iterrows():
            print(f"\n{row['Strategy']}")
            print(f"  Return:  {row['Baseline Return %']:>7.2f}% → {row['Optimized Return %']:>7.2f}% (Δ {row['Improvement %']:>+6.2f}%)")
            print(f"  Sharpe:  {row['Baseline Sharpe']:>7.2f}  → {row['Optimized Sharpe']:>7.2f}")
            print(f"  Trades:  {row['Baseline Trades']:>7.0f}  → {row['Optimized Trades']:>7.0f}")
        
        csv_path = output_dir / 'comparison.csv'
        df.to_csv(csv_path, index=False)
        
        print(f"\n{'='*100}")
        print(f"Average improvement: {df['Improvement %'].mean():+.2f}%")
        print(f"Best: {df['Improvement %'].max():+.2f}% ({df.loc[df['Improvement %'].idxmax(), 'Strategy']})")
        print(f"Comparison saved to: {csv_path}")
    
    print_header("VALIDATION PIPELINE COMPLETE")
    print(f"Results: {output_dir}\n")


if __name__ == '__main__':
    main()