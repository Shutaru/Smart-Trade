"""
Simple Validation - Single Strategy End-to-End Test
"""

import sys
import json
import subprocess
import yaml
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_cmd(cmd, desc):
    print(f"\n[Running] {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[OK] {desc}")
        return True, result.stdout
    else:
        print(f"[FAIL] {desc}")
        return False, result.stderr


def parse_json(output):
    """Parse JSON from output - extracts complete JSON object"""
    start = output.find('{')
    if start == -1:
        return None
    
    brace_count = 0
    end = -1
    
    for i in range(start, len(output)):
        if output[i] == '{':
            brace_count += 1
        elif output[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break
    
    if end == -1:
        return None
    
    try:
        result = json.loads(output[start:end])
        return result if 'ret_tot_pct' in result else None
    except:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy', default='bollinger_mean_reversion')
    parser.add_argument('--symbol', default='BTC/USDT:USDT')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--trials', type=int, default=10)
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('data/simple_validation') / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print(f"SIMPLE VALIDATION: {args.strategy}")
    print("="*80)
    print(f"Symbol: {args.symbol} | Days: {args.days} | Trials: {args.trials}\n")
    
    results = {}
    
    # STEP 1: Baseline
    print("="*80)
    print("STEP 1: BASELINE")
    print("="*80)
    
    with open('config.yaml', 'r') as f:
        cfg = yaml.safe_load(f)
    cfg['strategy'] = args.strategy
    cfg['symbol'] = args.symbol
    with open('config.yaml', 'w') as f:
        yaml.safe_dump(cfg, f)
    
    cmd = [sys.executable, 'optimization/backtest_engine.py', '--days', str(args.days)]
    success, output = run_cmd(cmd, "Baseline backtest")
    
    baseline_metrics = parse_json(output) if success else None
    if not baseline_metrics:
        print("[ERROR] Baseline failed - no valid JSON output!")
        return
    
    results['baseline'] = baseline_metrics
    print(f"\nBASELINE RESULTS:")
    print(f"  Return:  {baseline_metrics['ret_tot_pct']:>8.2f}%")
    print(f"  Sharpe:  {baseline_metrics['sharpe_ann']:>8.2f}")
    print(f"  Max DD:  {baseline_metrics['maxdd_pct']:>8.2f}%")
    print(f"  Trades:  {baseline_metrics['trades']:>8.0f}")
    
    # STEP 2: Optimization
    print("\n" + "="*80)
    print(f"STEP 2: OPTIMIZATION ({args.trials} trials)")
    print("="*80)
    
    cmd = [sys.executable, 'run_optimizer.py', '--strategy', args.strategy,
           '--symbol', args.symbol, '--trials', str(args.trials), '--days', str(args.days)]
    success, output = run_cmd(cmd, "Parameter optimization")
    
    opt_results = None
    if success:
        try:
            opt_dirs = list(Path('data/optimization').glob(f'opt_{args.strategy}_*'))
            if opt_dirs:
                latest = max(opt_dirs, key=lambda p: p.stat().st_mtime)
                with open(latest / 'optimization_results.json', 'r') as f:
                    opt_results = json.load(f)
        except:
            pass
    
    if not opt_results:
        print("[ERROR] Optimization failed!")
        return
    
    results['optimization'] = opt_results
    print(f"\nOPTIMIZATION RESULTS:")
    print(f"  Best Score: {opt_results['best_value']:.4f}")
    print(f"\n  Optimized Parameters:")
    for key, val in opt_results['best_params'].items():
        print(f"    {key}: {val}")
    
    # STEP 3: Post-optimization
    print("\n" + "="*80)
    print("STEP 3: POST-OPTIMIZATION")
    print("="*80)
    
    with open('config.yaml', 'r') as f:
        cfg = yaml.safe_load(f)
    cfg['strategy'] = args.strategy
    cfg['symbol'] = args.symbol
    if 'risk' not in cfg:
        cfg['risk'] = {}
    cfg['risk'].update(opt_results['best_params'])
    with open('config.yaml', 'w') as f:
        yaml.safe_dump(cfg, f)
    
    cmd = [sys.executable, 'optimization/backtest_engine.py', '--days', str(args.days)]
    success, output = run_cmd(cmd, "Post-optimization backtest")
    
    optimized_metrics = parse_json(output) if success else None
    if not optimized_metrics:
        print("[ERROR] Post-optimization failed!")
        return
    
    results['optimized'] = optimized_metrics
    print(f"\nPOST-OPTIMIZATION RESULTS:")
    print(f"  Return:  {optimized_metrics['ret_tot_pct']:>8.2f}%")
    print(f"  Sharpe:  {optimized_metrics['sharpe_ann']:>8.2f}")
    print(f"  Max DD:  {optimized_metrics['maxdd_pct']:>8.2f}%")
    print(f"  Trades:  {optimized_metrics['trades']:>8.0f}")
    
    # STEP 4: Comparison
    print("\n" + "="*80)
    print("COMPARISON: BEFORE vs AFTER")
    print("="*80)
    
    baseline = results['baseline']
    optimized = results['optimized']
    improvement = optimized['ret_tot_pct'] - baseline['ret_tot_pct']
    
    print(f"\n{'Metric':<20} {'Baseline':>12} {'Optimized':>12} {'Change':>12}")
    print("-" * 60)
    print(f"{'Return %':<20} {baseline['ret_tot_pct']:>12.2f} {optimized['ret_tot_pct']:>12.2f} {improvement:>+12.2f}")
    print(f"{'Sharpe':<20} {baseline['sharpe_ann']:>12.2f} {optimized['sharpe_ann']:>12.2f} {optimized['sharpe_ann']-baseline['sharpe_ann']:>+12.2f}")
    print(f"{'Max DD %':<20} {baseline['maxdd_pct']:>12.2f} {optimized['maxdd_pct']:>12.2f} {optimized['maxdd_pct']-baseline['maxdd_pct']:>+12.2f}")
    print(f"{'Trades':<20} {baseline['trades']:>12.0f} {optimized['trades']:>12.0f} {optimized['trades']-baseline['trades']:>+12.0f}")
    
    print(f"\n{'='*60}")
    if improvement > 0:
        print(f"SUCCESS: +{improvement:.2f}% improvement")
    else:
        print(f"REGRESSION: {improvement:.2f}% worse")
    print(f"{'='*60}\n")
    
    with open(output_dir / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_dir}/results.json\n")


if __name__ == '__main__':
    main()