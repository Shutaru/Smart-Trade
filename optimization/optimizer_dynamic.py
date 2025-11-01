"""
Dynamic Parameter Optimizer

Integrates dynamic indicators with Optuna optimizer.
Optimizes indicator parameters + exit parameters for any strategy.
"""

import optuna
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import sys
import os
import time
from datetime import datetime
from tqdm import tqdm

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimization.backtest_with_params import run_backtest_with_params, objective_function
from optimization.parameter_ranges import get_parameter_ranges_for_strategy
from strategies.registry import STRATEGY_METADATA
from core.indicator_cache import get_cache


class DynamicOptimizer:
    """
    Dynamic parameter optimizer using Optuna
    
    Optimizes both indicator parameters and exit parameters.
    """
    
    def __init__(
        self,
        strategy_name: str,
        df: pd.DataFrame,
        n_trials: int = 100,
        timeout: Optional[int] = None,
        use_cache: bool = True
    ):
        """
        Initialize optimizer
        
        Args:
            strategy_name: Name of strategy to optimize
            df: OHLCV DataFrame
            n_trials: Number of optimization trials (default: 100)
            timeout: Timeout in seconds (optional)
            use_cache: Use indicator cache (default: True)
        """
        self.strategy_name = strategy_name
        self.df = df
        self.n_trials = n_trials
        self.timeout = timeout
        self.use_cache = use_cache
        
        # Get parameter ranges
        metadata = STRATEGY_METADATA.get(strategy_name, {})
        self.param_ranges = get_parameter_ranges_for_strategy(strategy_name, metadata)
        
        # Study
        self.study: Optional[optuna.Study] = None
        self.best_params: Optional[Dict[str, Any]] = None
        self.best_score: Optional[float] = None
        
        # Cache
        self.cache = get_cache()
    
    def _objective(self, trial: optuna.Trial) -> float:
        """
        Optuna objective function
        
        Args:
            trial: Optuna trial
        
        Returns:
            Score (to maximize)
        """
        # Suggest parameters
        params = {}
        
        for param_range in self.param_ranges:
            if param_range.type == 'int':
                params[param_range.name] = trial.suggest_int(
                    param_range.name,
                    int(param_range.low),
                    int(param_range.high),
                    step=int(param_range.step) if param_range.step else 1
                )
            elif param_range.type == 'float':
                if param_range.log:
                    params[param_range.name] = trial.suggest_float(
                        param_range.name,
                        param_range.low,
                        param_range.high,
                        log=True
                    )
                else:
                    params[param_range.name] = trial.suggest_float(
                        param_range.name,
                        param_range.low,
                        param_range.high,
                        step=param_range.step if param_range.step else None
                    )
            elif param_range.type == 'categorical':
                params[param_range.name] = trial.suggest_categorical(
                    param_range.name,
                    param_range.choices
                )
        
        # Run backtest
        try:
            score = objective_function(params, self.df, self.strategy_name)
            
            # Store metrics as user attributes
            if score > -999.0:
                metrics = run_backtest_with_params(
                    self.df,
                    self.strategy_name,
                    params,
                    use_cache=self.use_cache
                )
                
                trial.set_user_attr('total_profit', metrics['total_profit'])
                trial.set_user_attr('sharpe', metrics['sharpe'])
                trial.set_user_attr('max_dd', metrics['max_dd'])
                trial.set_user_attr('trades', metrics['trades'])
                trial.set_user_attr('win_rate', metrics['win_rate'])
            
            return score
        
        except Exception as e:
            return -999.0
    
    def optimize(
        self,
        sampler: str = 'TPE',
        pruner: str = 'Median',
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Run optimization
        
        Args:
            sampler: Sampler type ('TPE', 'Random', 'CmaEs')
            pruner: Pruner type ('Median', 'Hyperband', None)
            show_progress: Show progress bar
        
        Returns:
            Dictionary with optimization results
        """
        
        # Create sampler
        if sampler == 'TPE':
            sampler_obj = optuna.samplers.TPESampler()
        elif sampler == 'Random':
            sampler_obj = optuna.samplers.RandomSampler()
        elif sampler == 'CmaEs':
            sampler_obj = optuna.samplers.CmaEsSampler()
        else:
            sampler_obj = optuna.samplers.TPESampler()
        
        # Create pruner
        if pruner == 'Median':
            pruner_obj = optuna.pruners.MedianPruner()
        elif pruner == 'Hyperband':
            pruner_obj = optuna.pruners.HyperbandPruner()
        else:
            pruner_obj = None
        
        # Create study
        study_name = f"opt_{self.strategy_name}_{int(time.time())}"
        
        # Suppress Optuna logging
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        
        self.study = optuna.create_study(
            study_name=study_name,
            direction='maximize',
            sampler=sampler_obj,
            pruner=pruner_obj
        )
        
        # Clear cache before optimization
        if self.use_cache:
            self.cache.clear()
        
        # Run optimization
        start_time = time.time()
        
        print(f"\n🚀 Starting optimization for '{self.strategy_name}'")
        print(f"   Trials: {self.n_trials}")
        print(f"   Parameters: {len(self.param_ranges)}")
        print(f"   Sampler: {sampler}")
        print(f"   Cache: {'ON' if self.use_cache else 'OFF'}")
        print("=" * 80)
        print()
        
        # Progress bar with tqdm
        with tqdm(
            total=self.n_trials,
            desc="🔬 Optimizing",
            bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
            ncols=100,
            disable=not show_progress
        ) as pbar:
            
            def progress_callback(study, trial):
                """Update progress bar after each trial"""
                pbar.update(1)
                
                # Update postfix with best score and last score
                best = study.best_value if study.best_value != float('-inf') else -999.0
                last = trial.value if trial.value != float('-inf') else -999.0
                
                pbar.set_postfix({
                    'best': f"{best:.2f}",
                    'last': f"{last:.2f}"
                })
            
            self.study.optimize(
                self._objective,
                n_trials=self.n_trials,
                timeout=self.timeout,
                callbacks=[progress_callback],
                show_progress_bar=False  # Disable Optuna's default bar
            )
        
        elapsed = time.time() - start_time
        
        # Get best results
        self.best_params = self.study.best_params
        self.best_score = self.study.best_value
        
        # Get best metrics
        best_trial = self.study.best_trial
        best_metrics = {
            'total_profit': best_trial.user_attrs.get('total_profit', 0),
            'sharpe': best_trial.user_attrs.get('sharpe', 0),
            'max_dd': best_trial.user_attrs.get('max_dd', 0),
            'trades': best_trial.user_attrs.get('trades', 0),
            'win_rate': best_trial.user_attrs.get('win_rate', 0)
        }
        
        # Print results
        print("\n" + "=" * 80)
        print("✅ OPTIMIZATION COMPLETE")
        print("=" * 80)
        
        print(f"\n⏱️  Time: {elapsed:.1f}s ({elapsed/self.n_trials:.2f}s per trial)")
        print(f"📊 Completed trials: {len(self.study.trials)}")
        print(f"✅ Best score: {self.best_score:.2f}")
        
        print(f"\n📈 Best Metrics:")
        print(f"   Total Profit: {best_metrics['total_profit']:>8.2f}%")
        print(f"   Sharpe:       {best_metrics['sharpe']:>8.2f}")
        print(f"   Max DD:       {best_metrics['max_dd']:>8.2f}%")
        print(f"   Trades:       {best_metrics['trades']:>8}")
        print(f"   Win Rate:     {best_metrics['win_rate']:>8.2f}%")
        
        print(f"\n🎯 Best Parameters ({len(self.best_params)}):")
        for key, val in sorted(self.best_params.items()):
            print(f"   {key:25s}: {val}")
        
        # Cache stats
        if self.use_cache:
            print("\n" + "=" * 80)
            self.cache.print_stats()
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'best_metrics': best_metrics,
            'n_trials': len(self.study.trials),
            'elapsed_seconds': elapsed,
            'study': self.study
        }
    
    def plot_optimization_history(self, save_path: Optional[str] = None):
        """Plot optimization history"""
        if self.study is None:
            raise ValueError("Run optimize() first")
        
        import matplotlib.pyplot as plt
        
        fig = optuna.visualization.matplotlib.plot_optimization_history(self.study)
        
        if save_path:
            plt.savefig(save_path)
            print(f"✅ Saved plot to {save_path}")
        else:
            plt.show()
    
    def plot_param_importances(self, save_path: Optional[str] = None):
        """Plot parameter importances"""
        if self.study is None:
            raise ValueError("Run optimize() first")
        
        import matplotlib.pyplot as plt
        
        try:
            fig = optuna.visualization.matplotlib.plot_param_importances(self.study)
            
            if save_path:
                plt.savefig(save_path)
                print(f"✅ Saved plot to {save_path}")
            else:
                plt.show()
        except Exception as e:
            print(f"⚠️  Could not plot importances: {e}")


if __name__ == '__main__':
    print("✅ Testing Dynamic Optimizer...")
    
    # Create test data
    dates = pd.date_range('2024-01-01', periods=2000, freq='5min')
    np.random.seed(42)
    
    # Create trending data
    trend = np.linspace(0, 2000, 2000)
    noise = np.random.randn(2000).cumsum() * 50
    base_price = 42000 + trend + noise
    
    df = pd.DataFrame({
        'open': base_price,
        'high': base_price + np.random.randint(10, 100, 2000),
        'low': base_price - np.random.randint(10, 100, 2000),
        'close': base_price + np.random.randn(2000) * 20,
        'volume': np.random.randint(100, 1000, 2000)
    }, index=dates)
    
    print("\n" + "=" * 80)
    print("TEST: Optimize bollinger_mean_reversion")
    print("=" * 80)
    
    # Create optimizer
    optimizer = DynamicOptimizer(
        strategy_name='bollinger_mean_reversion',
        df=df,
        n_trials=20,
        use_cache=True
    )
    
    # Run optimization
    results = optimizer.optimize(
        sampler='TPE',
        pruner='Median',
        show_progress=True
    )
    
    print("\n✅ Optimization test completed!")
    print(f"   Best score: {results['best_score']:.2f}")
    print(f"   Trials: {results['n_trials']}")
    print(f"   Time: {results['elapsed_seconds']:.1f}s")
    
    if results['best_score'] > 0:
        print("\n🎉 Found profitable parameters!")
    else:
        print("\n⚠️  No profitable parameters found (may need more trials or better data)")