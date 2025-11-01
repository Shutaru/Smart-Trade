"""
Complete Validation Pipeline

Runs full validation workflow:
1. Baseline backtest (4 years, TOP 3 strategies)
2. Optimization (50 trials each)
3. Post-optimization backtest
4. Comparison report

Usage:
    python run_validation_pipeline.py
    python run_validation_pipeline.py --symbol ETH/USDT --timeframe 1h
"""

import sys
import json
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def run_command(cmd, description):
    """Run command and capture output"""
    print(f"[Running] {description}...")
    print(f"[Command] {' '.join(cmd)}\n")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ {description} completed in {elapsed:.1f}s\n")
        return True, result.stdout, elapsed
    else:
        print(f"❌ {description} failed!")
        print(f"Error: {result.stderr}\n")
        return False, result.stderr, elapsed


def parse_json_output(output):
    """Parse JSON from command output"""
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
    parser.add_argument('--symbol', default='BTC/USDT:USDT', help='Trading symbol')
    parser.add_argument('--exchange', default='binance', help='Exchange')
 parser.add_argument('--timeframe', default='5m', help='Timeframe')
    parser.add_argument('--days', type=int, default=1460, help='Days to test (default: 4 years)')
    parser.add_argument('--trials', type=int, default=50, help='Optimization trials per strategy')
    
    args = parser.parse_args()
  
    # TOP 3 strategies from previous testing
    strategies = [
    'bollinger_mean_reversion',
        'cci_extreme_snapback',
        'vwap_institutional_trend'
    ]
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('data') / 'validation' / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print_header("COMPLETE VALIDATION PIPELINE")
    print(f"Timestamp: {timestamp}")
    print(f"Symbol: {args.symbol}")
    print(f"Exchange: {args.exchange}")
    print(f"Timeframe: {args.timeframe}")
  print(f"Period: {args.days} days (~{args.days/365:.1f} years)")
    print(f"Strategies: {', '.join(strategies)}")
    print(f"Optimization trials: {args.trials} per strategy")
    print(f"Output: {output_dir}")
    
    results = {
        'config': {
         'timestamp': timestamp,
        'symbol': args.symbol,
      'exchange': args.exchange,
          'timeframe': args.timeframe,
            'days': args.days,
            'trials': args.trials,
            'strategies': strategies
},
    'baseline': {},
        'optimization': {},
        'post_optimization': {}
    }
    
  # ========================================================================
    # STEP 1: BASELINE BACKTEST
    # ========================================================================
    print_header(f"STEP 1: BASELINE BACKTEST ({args.days} days)")
    
    baseline_results = {}
  
    for strategy in strategies:
    cmd = [
   sys.executable,
          'optimization/backtest_engine.py',
            '--days', str(args.days)
        ]
        
        # Update config with strategy
        import yaml
        with open('config.yaml', 'r') as f:
    cfg = yaml.safe_load(f)
        
        cfg['strategy'] = strategy
        cfg['symbol'] = args.symbol
        cfg['exchange'] = args.exchange
      cfg['timeframe'] = args.timeframe
        
        with open('config.yaml', 'w') as f:
            yaml.safe_dump(cfg, f)
        
success, output, elapsed = run_command(cmd, f"Baseline: {strategy}")
        
        if success:
     metrics = parse_json_output(output)
        if metrics and 'error' not in metrics:
         baseline_results[strategy] = {
       'metrics': metrics,
 'elapsed': elapsed
    }
     print(f"  Return: {metrics['ret_tot_pct']:.2f}%")
   print(f"  Sharpe: {metrics['sharpe_ann']:.2f}")
         print(f"  Trades: {metrics['trades']}")
                print()
   else:
     baseline_results[strategy] = {'error': metrics.get('error', 'Unknown error')}
        else:
      baseline_results[strategy] = {'error': output}
    
    results['baseline'] = baseline_results
    
    # Save intermediate results
    with open(output_dir / 'results_step1_baseline.json', 'w') as f:
      json.dump(results, f, indent=2)
  
    # ========================================================================
    # STEP 2: OPTIMIZATION
    # ========================================================================
    print_header(f"STEP 2: OPTIMIZATION ({args.trials} trials per strategy)")
    
    optimization_results = {}
    
    for strategy in strategies:
        print(f"\n{'─'*80}")
        print(f"Optimizing: {strategy}")
 print(f"{'─'*80}\n")
        
        cmd = [
            sys.executable,
    'run_optimizer.py',
     '--strategy', strategy,
        '--symbol', args.symbol,
            '--exchange', args.exchange,
 '--timeframe', args.timeframe,
            '--trials', str(args.trials),
    '--days', str(args.days)
        ]
        
  success, output, elapsed = run_command(cmd, f"Optimize: {strategy}")
        
        if success:
       # Parse optimization results
            # Look for JSON output in stdout
            opt_results = None
            for line in output.split('\n'):
        if 'Best Score:' in line:
try:
         score = float(line.split(':')[1].strip())
  opt_results = {'best_score': score}
         except:
         pass
 
        # Try to load from optimization output directory
      try:
# Find latest optimization directory
 opt_dirs = list(Path('data/optimization').glob(f'opt_{strategy}_*'))
 if opt_dirs:
  latest_opt = max(opt_dirs, key=lambda p: p.stat().st_mtime)
       results_file = latest_opt / 'optimization_results.json'
       if results_file.exists():
       with open(results_file, 'r') as f:
             opt_results = json.load(f)
            except Exception as e:
  print(f"  Warning: Could not load optimization results: {e}")

  optimization_results[strategy] = {
       'results': opt_results,
             'elapsed': elapsed,
                'output_snippet': output[-500:] if len(output) > 500 else output
            }
       
    if opt_results:
         print(f"  Best Score: {opt_results.get('best_value', 'N/A')}")
       print(f"  Best Return: {opt_results.get('best_metrics', {}).get('return', 'N/A')}")
             print()
        else:
            optimization_results[strategy] = {'error': output}
    
    results['optimization'] = optimization_results
    
    # Save intermediate results
    with open(output_dir / 'results_step2_optimization.json', 'w') as f:
      json.dump(results, f, indent=2)
    
    # ========================================================================
    # STEP 3: POST-OPTIMIZATION BACKTEST
    # ========================================================================
    print_header("STEP 3: POST-OPTIMIZATION BACKTEST")
    
print("⚠️  Note: This requires manually applying optimized parameters to config.yaml")
    print("    For automated testing, we'll use the optimized parameters programmatically\n")
    
  post_opt_results = {}
  
for strategy in strategies:
        # Load optimized parameters
        opt_data = optimization_results.get(strategy, {}).get('results')
        if not opt_data or 'best_params' not in opt_data:
       print(f"  Skipping {strategy}: No optimized parameters found")
            continue
   
        # Update config with optimized parameters
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
   
        cfg['strategy'] = strategy
        cfg['symbol'] = args.symbol
        cfg['exchange'] = args.exchange
        cfg['timeframe'] = args.timeframe
        
        # Apply optimized risk parameters
    if 'risk' not in cfg:
       cfg['risk'] = {}
        
      for key, value in opt_data['best_params'].items():
      cfg['risk'][key] = value
     
        with open('config.yaml', 'w') as f:
          yaml.safe_dump(cfg, f)
        
      # Run backtest with optimized parameters
        cmd = [
         sys.executable,
         'optimization/backtest_engine.py',
'--days', str(args.days)
        ]
   
        success, output, elapsed = run_command(cmd, f"Post-opt: {strategy}")
        
        if success:
            metrics = parse_json_output(output)
            if metrics and 'error' not in metrics:
           post_opt_results[strategy] = {
           'metrics': metrics,
     'elapsed': elapsed,
          'optimized_params': opt_data['best_params']
         }
                print(f"  Return: {metrics['ret_tot_pct']:.2f}%")
                print(f"  Sharpe: {metrics['sharpe_ann']:.2f}")
         print(f"  Trades: {metrics['trades']}")
       print()
            else:
           post_opt_results[strategy] = {'error': metrics.get('error', 'Unknown error')}
        else:
    post_opt_results[strategy] = {'error': output}
    
results['post_optimization'] = post_opt_results
    
    # Save final results
    with open(output_dir / 'validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # ========================================================================
    # STEP 4: GENERATE COMPARISON REPORT
    # ========================================================================
    print_header("STEP 4: COMPARISON REPORT")
    
    # Build comparison table
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
                'Optimized Trades': post_opt.get('trades', 0),
       'Baseline Max DD %': baseline.get('maxdd_pct', 0),
      'Optimized Max DD %': post_opt.get('maxdd_pct', 0)
   }
      comparison.append(row)
    
    if comparison:
        df = pd.DataFrame(comparison)
        
    # Print table
  print("\n" + "="*120)
        print("BEFORE vs AFTER OPTIMIZATION")
        print("="*120 + "\n")
        
   for _, row in df.iterrows():
 print(f"\n{row['Strategy']}")
   print(f"{'─'*80}")
            print(f"  Return:     {row['Baseline Return %']:>8.2f}%  →  {row['Optimized Return %']:>8.2f}%  (Δ {row['Improvement %']:>+7.2f}%)")
    print(f"  Sharpe:     {row['Baseline Sharpe']:>8.2f}     →  {row['Optimized Sharpe']:>8.2f}")
            print(f"  Trades:     {row['Baseline Trades']:>8.0f} →  {row['Optimized Trades']:>8.0f}")
          print(f"  Max DD:     {row['Baseline Max DD %']:>8.2f}%  →  {row['Optimized Max DD %']:>8.2f}%")
     
        # Save CSV
        csv_path = output_dir / 'comparison.csv'
        df.to_csv(csv_path, index=False)
        
        # Summary stats
        print(f"\n{'='*120}")
        print("SUMMARY")
    print(f"{'='*120}\n")
      print(f"Average return improvement: {df['Improvement %'].mean():+.2f}%")
        print(f"Best improvement: {df['Improvement %'].max():+.2f}% ({df.loc[df['Improvement %'].idxmax(), 'Strategy']})")
        print(f"Worst improvement: {df['Improvement %'].min():+.2f}% ({df.loc[df['Improvement %'].idxmin(), 'Strategy']})")
   
        print(f"\nComparison saved to: {csv_path}")
    else:
     print("⚠️  No valid comparisons available")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
 print_header("VALIDATION PIPELINE COMPLETE")
    
    print(f"Results saved to: {output_dir}")
    print(f"\nFiles generated:")
    print(f"  - validation_results.json (complete data)")
    print(f"  - comparison.csv (side-by-side comparison)")
    print(f"  - results_step1_baseline.json (baseline metrics)")
    print(f"  - results_step2_optimization.json (optimization data)")
    
 print(f"\n{'='*80}")
    print("Next Steps:")
    print("  1. Review comparison.csv for performance improvements")
    print("2. Analyze optimization_results.json for best parameters")
    print("  3. Apply best parameters to production config")
    print("  4. Run forward testing with optimized parameters")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
