"""
Apply Optimization Results to Config

Automatically applies best parameters from optimization to config.yaml
"""

import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any


def find_latest_optimization(strategy_name: str) -> Path:
    """Find most recent optimization results for strategy"""
    opt_dir = Path("data") / "optimization"
    
    if not opt_dir.exists():
        raise FileNotFoundError(f"No optimization directory found: {opt_dir}")
    
    # Find all optimization result files for this strategy
    candidates = list(opt_dir.glob(f"*{strategy_name}*/optimization_results.json"))
    
    if not candidates:
        raise FileNotFoundError(f"No optimization results found for {strategy_name}")
  
    # Get most recent
  latest = max(candidates, key=lambda p: p.stat().st_mtime)
    
    return latest


def load_optimization_results(results_file: Path) -> Dict[str, Any]:
    """Load optimization results from JSON"""
    with open(results_file, 'r') as f:
        return json.load(f)


def apply_parameters_to_config(params: Dict[str, Any], config_path: str = "config.yaml"):
    """Apply optimized parameters to config.yaml"""
    
    # Load current config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create backup
    backup_path = f"{config_path}.backup_{int(time.time())}"
    with open(backup_path, 'w') as f:
     yaml.safe_dump(config, f)
    
    print(f"[Apply] Created backup: {backup_path}")
    
    # Ensure risk section exists
    if 'risk' not in config:
        config['risk'] = {}
    
    # Apply each parameter
  changes = []
    for param_name, param_value in params.items():
        old_value = config['risk'].get(param_name)
        config['risk'][param_name] = param_value
        
        if old_value != param_value:
         changes.append({
   'param': param_name,
     'old': old_value,
        'new': param_value
     })
    
    # Save updated config
    with open(config_path, 'w') as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    
    print(f"[Apply] Updated {config_path}")
    print(f"[Apply] Changes made: {len(changes)}")
    
    for change in changes:
   print(f"  - {change['param']}: {change['old']} ? {change['new']}")
  
    return changes


def main():
    parser = argparse.ArgumentParser(
      description='Apply optimization results to config.yaml'
 )
    parser.add_argument(
        '--strategy',
        type=str,
   required=True,
        help='Strategy name (e.g., obv_range_fade)'
    )
    parser.add_argument(
  '--results-file',
        type=str,
 help='Path to optimization_results.json (optional, auto-finds if not specified)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Config file to update (default: config.yaml)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show changes without applying them'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("APPLY OPTIMIZATION RESULTS")
    print("="*80 + "\n")
    
    # Find or load results
    if args.results_file:
   results_file = Path(args.results_file)
    else:
        print(f"[Apply] Finding latest optimization for: {args.strategy}")
        results_file = find_latest_optimization(args.strategy)
    
    print(f"[Apply] Loading results from: {results_file}")
    
    # Load results
    results = load_optimization_results(results_file)
    
    # Extract info
    strategy_name = results.get('strategy_name', 'Unknown')
    best_params = results.get('best_params', {})
    best_metrics = results.get('best_metrics', {})
    
    print(f"\n?? Optimization Summary:")
    print(f"   Strategy: {strategy_name}")
    print(f" Best Sharpe: {best_metrics.get('sharpe', 0):.2f}")
    print(f"   Best Return: {best_metrics.get('return', 0):.2f}%")
    print(f"   Max DD: {best_metrics.get('max_dd', 0):.2f}%")
    print(f"   Trades: {best_metrics.get('trades', 0)}")
    print(f"   Win Rate: {best_metrics.get('win_rate', 0):.1f}%")
    
    print(f"\n?? Best Parameters:")
    for param_name, param_value in best_params.items():
        if isinstance(param_value, float):
     print(f"   {param_name}: {param_value:.2f}")
        else:
         print(f"   {param_name}: {param_value}")
    
    if args.dry_run:
      print(f"\n??  DRY RUN - No changes will be made")
        print(f"   Remove --dry-run to apply changes")
        return
    
    # Confirm
    response = input(f"\nApply these parameters to {args.config}? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("? Cancelled by user")
  return
    
    # Apply changes
    import time
    changes = apply_parameters_to_config(best_params, args.config)
    
    print(f"\n? Applied {len(changes)} parameter(s) to {args.config}")
    print(f"\n?? Next steps:")
    print(f"   1. Review changes: vimdiff {args.config} {args.config}.backup_*")
    print(f"   2. Run backtest: python backtest.py --days 365")
    print(f"   3. Paper trade: python agent_runner.py --config configs/agent_paper.yaml")
    print()


if __name__ == '__main__':
    main()
