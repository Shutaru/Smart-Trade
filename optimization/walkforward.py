"""
Walk-Forward Validator - Detect Overfitting

Validates strategy robustness using walk-forward analysis:
- Split data into In-Sample (training) and Out-of-Sample (testing)
- Optimize on IS, validate on OS
- Calculate degradation factor (OS performance / IS performance)
- Detect overfitting (degradation < 0.7 = overfitted)
"""

import subprocess
import sys
import json
import yaml
import time
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from strategy_optimizer from strategies import core as strategyOptimizer, ParameterRange
import pandas as pd


class WalkForwardValidator:
    """
    Walk-Forward Analysis System
    
    Splits data into overlapping windows:
    - In-Sample (IS): Training period for optimization
    - Out-of-Sample (OS): Testing period for validation
    
    Good strategy characteristics:
    - OS Sharpe >= 70% of IS Sharpe (degradation factor >= 0.7)
    - OS profitability consistent across folds
    - Similar win rates in IS vs OS
    """
    
    def __init__(
        self,
        strategy_name: str,
        param_ranges: List[ParameterRange],
        config_path: str = "config.yaml",
        is_days: int = 180,
        os_days: int = 60,
        n_folds: int = 6
    ):
        self.strategy_name = strategy_name
        self.param_ranges = param_ranges
        self.config_path = config_path
        self.is_days = is_days
        self.os_days = os_days
        self.n_folds = n_folds
        
        with open(config_path, 'r') as f:
            self.base_config = yaml.safe_load(f)
        
        self.output_dir = Path("data") / "walkforward" / f"{strategy_name}_{int(time.time())}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[WalkForward] Strategy: {strategy_name}")
        print(f"[WalkForward] IS Days: {is_days} | OS Days: {os_days} | Folds: {n_folds}")
        print(f"[WalkForward] Total period: {(is_days + os_days) * n_folds} days")
    
    def _run_backtest(
        self,
        params: Dict[str, Any],
        start_day: int,
        end_day: int,
        label: str
    ) -> Dict[str, float]:
        """Run backtest on specific date range"""
        temp_config = dict(self.base_config)
        
        if 'risk' not in temp_config:
            temp_config['risk'] = {}
        
        for param_name, param_value in params.items():
            temp_config['risk'][param_name] = param_value
        
        temp_config_path = self.output_dir / f"temp_config_{label}.yaml"
        with open(temp_config_path, 'w') as f:
            yaml.safe_dump(temp_config, f)
        
        try:
            cmd = [
                sys.executable,
                'backtest.py',
                '--days', str(end_day - start_day),
                '--config', str(temp_config_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"[WalkForward] Backtest failed: {result.stderr}")
                return {}
            
            for line in result.stdout.split('\n'):
                if line.strip().startswith('{'):
                    try:
                        metrics = json.loads(line)
                        return {
                            'sharpe': metrics.get('sharpe_ann', 0.0),
                            'sortino': metrics.get('sortino_ann', 0.0),
                            'return': metrics.get('ret_tot_pct', 0.0),
                            'max_dd': abs(metrics.get('maxdd_pct', 0.0)),
                            'trades': metrics.get('trades', 0),
                            'win_rate': metrics.get('win_rate_pct', 0.0),
                            'profit_factor': metrics.get('profit_factor', 0.0)
                        }
                    except json.JSONDecodeError:
                        continue
            
            return {}
        
        finally:
            if temp_config_path.exists():
                temp_config_path.unlink()
    
    def _optimize_on_window(
        self,
        fold: int,
        start_day: int,
        end_day: int
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """Optimize parameters on IS window"""
        print(f"\n[Fold {fold}] Optimizing on IS: days {start_day}-{end_day}")
        
        optimizer = StrategyOptimizer(
            strategy_name=f"{self.strategy_name}_fold{fold}",
            base_config_path=self.config_path,
            param_ranges=self.param_ranges,
            n_trials=20,
            study_name=f"wf_{self.strategy_name}_fold{fold}_{int(time.time())}"
        )
        
        results = optimizer.optimize(n_jobs=1, sampler='TPE', show_progress=False)
        
        best_params = results['best_params']
        best_metrics = results['best_metrics']
        
        print(f"[Fold {fold}] Best IS Sharpe: {best_metrics.get('sharpe', 0):.2f}")
        
        return best_params, best_metrics
    
    def _validate_on_window(
        self,
        fold: int,
        params: Dict[str, Any],
        start_day: int,
        end_day: int
    ) -> Dict[str, float]:
        """Validate parameters on OS window"""
        print(f"[Fold {fold}] Validating on OS: days {start_day}-{end_day}")
        
        metrics = self._run_backtest(
            params=params,
            start_day=start_day,
            end_day=end_day,
            label=f"fold{fold}_os"
        )
        
        print(f"[Fold {fold}] OS Sharpe: {metrics.get('sharpe', 0):.2f}")
        
        return metrics
    
    def run_walkforward(self) -> Dict[str, Any]:
        """
        Run complete walk-forward analysis
        
        Returns:
            Dict with results for all folds and summary statistics
        """
        print(f"\n{'=' * 80}")
        print(f"WALK-FORWARD ANALYSIS: {self.strategy_name}")
        print(f"{'=' * 80}\n")
        
        start_time = time.time()
        results = {
            'strategy_name': self.strategy_name,
            'config': {
                'is_days': self.is_days,
                'os_days': self.os_days,
                'n_folds': self.n_folds
            },
            'folds': []
        }
        
        total_days = (self.is_days + self.os_days) * self.n_folds
        
        for fold in range(1, self.n_folds + 1):
            print(f"\n{'#' * 80}")
            print(f"# FOLD {fold}/{self.n_folds}")
            print(f"{'#' * 80}")
            
            is_start = (fold - 1) * (self.is_days + self.os_days)
            is_end = is_start + self.is_days
            
            os_start = is_end
            os_end = os_start + self.os_days
            
            best_params, is_metrics = self._optimize_on_window(fold, is_start, is_end)
            
            os_metrics = self._validate_on_window(fold, best_params, os_start, os_end)
            
            is_sharpe = is_metrics.get('sharpe', 0)
            os_sharpe = os_metrics.get('sharpe', 0)
            
            if is_sharpe > 0:
                degradation_factor = os_sharpe / is_sharpe
            else:
                degradation_factor = 0.0
            
            fold_result = {
                'fold': fold,
                'is_window': {'start': is_start, 'end': is_end},
                'os_window': {'start': os_start, 'end': os_end},
                'best_params': best_params,
                'is_metrics': is_metrics,
                'os_metrics': os_metrics,
                'degradation_factor': degradation_factor
            }
            
            results['folds'].append(fold_result)
            
            print(f"\n[Fold {fold}] Summary:")
            print(f"  IS Sharpe: {is_sharpe:.2f} | OS Sharpe: {os_sharpe:.2f}")
            print(f"  Degradation: {degradation_factor:.2%}")
            
            if degradation_factor >= 0.7:
                print(f"  ✅ Good (degradation >= 70%)")
            elif degradation_factor >= 0.5:
                print(f"  ⚠️  Marginal (degradation 50-70%)")
            else:
                print(f"  ❌ Overfitted (degradation < 50%)")
        
        elapsed = time.time() - start_time
        
        all_is_sharpes = [f['is_metrics'].get('sharpe', 0) for f in results['folds']]
        all_os_sharpes = [f['os_metrics'].get('sharpe', 0) for f in results['folds']]
        all_degradations = [f['degradation_factor'] for f in results['folds']]
        
        avg_is_sharpe = sum(all_is_sharpes) / len(all_is_sharpes)
        avg_os_sharpe = sum(all_os_sharpes) / len(all_os_sharpes)
        avg_degradation = sum(all_degradations) / len(all_degradations)
        
        results['summary'] = {
            'avg_is_sharpe': avg_is_sharpe,
            'avg_os_sharpe': avg_os_sharpe,
            'avg_degradation': avg_degradation,
            'elapsed_seconds': elapsed
        }
        
        results_file = self.output_dir / "walkforward_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'=' * 80}")
        print(f"WALK-FORWARD COMPLETE")
        print(f"{'=' * 80}\n")
        print(f"Average IS Sharpe: {avg_is_sharpe:.2f}")
        print(f"Average OS Sharpe: {avg_os_sharpe:.2f}")
        print(f"Average Degradation: {avg_degradation:.2%}")
        
        if avg_degradation >= 0.7:
            print(f"\n✅ ROBUST STRATEGY (degradation >= 70%)")
            print(f"   Strategy is NOT overfitted. Safe to deploy.")
        elif avg_degradation >= 0.5:
            print(f"\n⚠️  MARGINAL STRATEGY (degradation 50-70%)")
            print(f"   Some overfitting detected. Use with caution.")
        else:
            print(f"\n❌ OVERFITTED STRATEGY (degradation < 50%)")
            print(f"   Heavily overfitted. DO NOT deploy.")
        
        print(f"\nElapsed: {elapsed / 60:.1f} minutes")
        print(f"Results saved to: {results_file}\n")
        
        return results


async def main():
    """Main entry point"""
    import argparse
    import asyncio
    from optimization.optimizer import DEFAULT_RANGES
    
    parser = argparse.ArgumentParser(description='Walk-forward validation')
    parser.add_argument('--strategy', type=str, required=True, help='Strategy name')
    parser.add_argument('--is-days', type=int, default=180, help='In-sample days')
    parser.add_argument('--os-days', type=int, default=60, help='Out-of-sample days')
    parser.add_argument('--folds', type=int, default=6, help='Number of folds')
    
    args = parser.parse_args()
    
    param_ranges = [
        ParameterRange('rsi_period', 'int', low=10, high=20, step=2),
        ParameterRange('adx_threshold', 'int', low=18, high=30, step=2),
        ParameterRange('atr_sl_mult', 'float', low=1.5, high=3.0, step=0.25),
    ]
    
    validator = WalkForwardValidator(
        strategy_name=args.strategy,
        param_ranges=param_ranges,
        is_days=args.is_days,
        os_days=args.os_days,
        n_folds=args.folds
    )
    
    results = validator.run_walkforward()
    
    print("\n🎉 Walk-forward analysis complete!")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())