"""
Strategy Optimizer - Optuna-based Parameter Optimization

NEW: Multi-Symbol & Multi-Timeframe Support!

Optimizes strategy parameters using Bayesian optimization (Optuna).
Uses PROFIT-FIRST scoring (same as discovery engine).
"""

import optuna
import subprocess
import sys
import json
import yaml
import time
import os
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ParameterRange:
    """Define parameter search space"""
    name: str
    type: str  # 'int', 'float', 'categorical'
    low: Optional[float] = None
    high: Optional[float] = None
    step: Optional[float] = None
    choices: Optional[List[Any]] = None
    log: bool = False


class StrategyOptimizer:
    """
    Optimize strategy parameters using Optuna
    
    NEW: Now supports dynamic symbol, exchange, and timeframe!
    
    Features:
    - Bayesian optimization (TPE sampler)
    - PROFIT-FIRST scoring (70% return, 10% Sortino, constraints)
    - Comprehensive parameter ranges for all indicators
    - Parallel trials support
    - Multi-symbol/timeframe support
    """
    
    def __init__(
        self,
        strategy_name: str,
        base_config_path: str = "config.yaml",
        symbol: str = None,
        exchange: str = None,
        timeframe: str = None,
        param_ranges: List[ParameterRange] = None,
        n_trials: int = 50,
        study_name: Optional[str] = None,
        storage: Optional[str] = None
    ):
        self.strategy_name = strategy_name
        self.base_config_path = base_config_path
        self.param_ranges = param_ranges or []
        self.n_trials = n_trials
        
        # Load base config
        with open(base_config_path, 'r') as f:
            self.base_config = yaml.safe_load(f)
        
        # Override with provided parameters
        if symbol:
            self.base_config['symbol'] = symbol
        if exchange:
            self.base_config['exchange'] = exchange
        if timeframe:
            self.base_config['timeframe'] = timeframe
        
        # Store current configuration
        self.symbol = self.base_config.get('symbol', 'BTC/USDT:USDT')
        self.exchange = self.base_config.get('exchange', 'binance')
        self.timeframe = self.base_config.get('timeframe', '5m')
        
        # Setup Optuna study
        sym_safe = self.symbol.replace('/', '_').replace(':', '_')
        self.study_name = study_name or f"opt_{strategy_name}_{sym_safe}_{self.timeframe}_{int(time.time())}"
        self.storage = storage or f"sqlite:///data/optimization/{self.study_name}.db"
        
        # Create output directory
        self.output_dir = Path("data") / "optimization" / self.study_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[Optimizer] Initialized:")
        print(f"  Strategy: {strategy_name}")
        print(f"  Symbol: {self.symbol}")
        print(f"  Exchange: {self.exchange}")
        print(f"  Timeframe: {self.timeframe}")
        print(f"  Study: {self.study_name}")
        print(f"  Objective: PROFIT-FIRST scoring (70% return, 10% Sortino, constraints)")
        print(f"  Trials: {n_trials}")
    
    def _suggest_parameter(self, trial: optuna.Trial, param: ParameterRange) -> Any:
        """Suggest parameter value for trial"""
        if param.type == 'int':
            if param.log:
                return trial.suggest_int(param.name, int(param.low), int(param.high), log=True)
            else:
                return trial.suggest_int(param.name, int(param.low), int(param.high), step=param.step or 1)
        
        elif param.type == 'float':
            if param.log:
                return trial.suggest_float(param.name, param.low, param.high, log=True)
            else:
                return trial.suggest_float(param.name, param.low, param.high, step=param.step)
        
        elif param.type == 'categorical':
            return trial.suggest_categorical(param.name, param.choices)
        
        else:
            raise ValueError(f"Unknown parameter type: {param.type}")
    
    def _run_backtest(self, params: Dict[str, Any], days: int = 365) -> Dict[str, float]:
        """Run backtest with given parameters"""
        # Create temporary config with optimized parameters
        temp_config = dict(self.base_config)
        
        # Set strategy name
        temp_config['strategy'] = self.strategy_name
      
        # Apply parameters to config
        if 'risk' not in temp_config:
            temp_config['risk'] = {}
        
        for param_name, param_value in params.items():
            temp_config['risk'][param_name] = param_value
        
        # Backup original config and save temp config
        config_backup = Path(self.base_config_path + '.backup')
        original_config_path = Path(self.base_config_path)
        
        try:
            # Backup original
            if original_config_path.exists():
                import shutil
                shutil.copy(original_config_path, config_backup)
            
            # Write temporary config
            with open(original_config_path, 'w') as f:
                yaml.safe_dump(temp_config, f)
            
            # Run backtest using optimization engine
            cmd = [
                sys.executable,
                'optimization/backtest_engine.py',
                '--config', str(original_config_path),
                '--days', str(days)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"[Optimizer] Backtest failed: {result.stderr}")
                return {'sharpe': -999.0, 'return': -999.0, 'max_dd': -999.0}
            
            # Parse results
            output = result.stdout
            
            # Try to parse JSON from output
            for line in output.split('\n'):
                if line.strip().startswith('{'):
                    try:
                        metrics = json.loads(line)
                        return {
                            'sharpe': metrics.get('sharpe_ann', 0.0),
                            'sortino': metrics.get('sortino_ann', metrics.get('sharpe_ann', 0.0) * 1.2),
                            'return': metrics.get('ret_tot_pct', 0.0),
                            'max_dd': abs(metrics.get('maxdd_pct', 0.0)),
                            'trades': metrics.get('trades', 0),
                            'win_rate': metrics.get('win_rate_pct', 0.0),
                            'profit_factor': metrics.get('profit_factor', 0.0)
                        }
                    except json.JSONDecodeError:
                        continue
            
            print(f"[Optimizer] Could not parse backtest output")
            return {'sharpe': -999.0, 'return': -999.0, 'max_dd': -999.0}
        
        finally:
            # Restore original config
            if config_backup.exists():
                import shutil
                shutil.move(config_backup, original_config_path)
            elif original_config_path.exists():
                original_config_path.unlink()
    
    def _objective_function(self, trial: optuna.Trial) -> float:
        """
        Objective function for Optuna
        
        Uses same PROFIT-FIRST scoring as discovery engine:
        - Return: 70%
        - Sortino: 10%
        - Win Rate: 10%
        - Trades: 5%
        - DD Penalty: 5% (only if > 15%)
        """
        # Suggest parameters
        params = {}
        for param_range in self.param_ranges:
            params[param_range.name] = self._suggest_parameter(trial, param_range)
        
        # Run backtest
        metrics = self._run_backtest(params)
        
        # Store metrics in trial user attributes
        for key, value in metrics.items():
            trial.set_user_attr(key, value)
        
        # Apply PROFIT-FIRST scoring v5 (ALIGNED WITH RANKER.PY)
        # Constraints (only 2 - same as discovery engine):
        # 1. Minimum trades for statistical significance
        # 2. Maximum drawdown for risk control
        # NO Sharpe constraint - let profitable strategies through!
        
        if metrics.get('trades', 0) < 5:  # Relaxed from 10 to 5
            return -999.0
        if abs(metrics.get('max_dd', 0)) > 50:
            return -999.0
        
        # NO SHARPE CONSTRAINT!
        # High return with low Sharpe (0.3-0.8) is common in crypto
        # We score it but don't reject it
        
        # Components (aligned with ranker.py PROFIT-FIRST v5)
        ret = metrics.get('return', 0)
        sharpe = metrics.get('sharpe', 0)
        sortino = metrics.get('sortino', metrics.get('sharpe', 0) * 1.2)
        win_rate = metrics.get('win_rate', 0)
        
        # Calculate score (95-2.5-1.25-1.25 split)
        # 1. RETURN (95 points max) - KING! NO PENALTY!
        return_component = 0.95 * ret
        
        # 2. SHARPE (2.5 points max) - Plateau at 2.0
        sharpe_normalized = max(0.0, min(sharpe / 2.0, 1.0))
        sharpe_component = 2.5 * sharpe_normalized
        
        # 3. SORTINO (1.25 points max)
        sortino_component = 1.25 * min(sortino / 8.0, 1.0)
    
        # 4. WIN RATE (1.25 points max)
        win_rate_component = 1.25 * (win_rate / 100.0)
    
        score = (
            return_component +
            sharpe_component +
            sortino_component +
            win_rate_component
        )
        
        return score
    
    def optimize(
        self,
        n_jobs: int = 1,
        sampler: str = 'TPE',
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Run optimization
        
        Args:
            n_jobs: Number of parallel trials (1 = sequential)
            sampler: 'TPE' (Bayesian) or 'Grid' (exhaustive)
            show_progress: Show progress bar
        
        Returns:
            Dict with best parameters, metrics, and study results
        """
        print(f"\n{'='*80}")
        print(f"STARTING OPTIMIZATION: {self.strategy_name}")
        print(f"{'='*80}\n")
        
        # Create Optuna study
        if sampler == 'TPE':
            sampler_obj = optuna.samplers.TPESampler(seed=42)
        elif sampler == 'Grid':
            sampler_obj = optuna.samplers.GridSampler()
        else:
            sampler_obj = optuna.samplers.TPESampler(seed=42)
        
        study = optuna.create_study(
            study_name=self.study_name,
            storage=self.storage,
            direction='maximize',
            sampler=sampler_obj,
            load_if_exists=True
        )
        
        # Run optimization
        start_time = time.time()
        
        study.optimize(
            self._objective_function,
            n_trials=self.n_trials,
            n_jobs=n_jobs,
            show_progress_bar=show_progress
        )
        
        elapsed = time.time() - start_time
        
        # Get best trial
        best_trial = study.best_trial
        
        results = {
            'strategy_name': self.strategy_name,
            'study_name': self.study_name,
            'best_params': best_trial.params,
            'best_value': best_trial.value,
            'best_metrics': {
                key: best_trial.user_attrs[key]
                for key in ['sharpe', 'sortino', 'return', 'max_dd', 'trades', 'win_rate', 'profit_factor']
                if key in best_trial.user_attrs
            },
            'n_trials': len(study.trials),
            'elapsed_seconds': elapsed
        }
        
        # Save results
        results_file = self.output_dir / "optimization_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"OPTIMIZATION COMPLETE")
        print(f"{'='*80}\n")
        print(f"Best score (PROFIT-FIRST): {best_trial.value:.4f}")
        print(f"Best parameters:")
        for key, value in best_trial.params.items():
            print(f"  {key}: {value}")
        print(f"\nMetrics:")
        for key, value in results['best_metrics'].items():
            print(f"  {key}: {value:.2f}")
        print(f"\nElapsed: {elapsed/60:.1f} minutes")
        print(f"Results saved to: {results_file}")
        print()
        
        return results
    
    def get_study(self) -> optuna.Study:
        """Load existing study"""
        return optuna.load_study(
            study_name=self.study_name,
            storage=self.storage
        )


# ============================================================================
# COMPREHENSIVE PARAMETER RANGES - ALL INDICATORS
# ============================================================================

DEFAULT_RANGES = {
    # RSI (Relative Strength Index)
    'rsi': [
        ParameterRange('rsi_period', 'int', low=7, high=28, step=1),
        ParameterRange('rsi_oversold', 'int', low=15, high=35, step=5),
        ParameterRange('rsi_overbought', 'int', low=65, high=85, step=5),
    ],
    
    # EMA (Exponential Moving Average)
    'ema': [
        ParameterRange('ema_fast', 'int', low=8, high=25, step=1),
        ParameterRange('ema_slow', 'int', low=30, high=100, step=5),
        ParameterRange('ema_trend', 'int', low=100, high=250, step=10),
    ],
    
    # SMA (Simple Moving Average)
    'sma': [
        ParameterRange('sma_fast', 'int', low=10, high=30, step=2),
        ParameterRange('sma_slow', 'int', low=40, high=120, step=5),
        ParameterRange('sma_trend', 'int', low=150, high=250, step=10),
    ],
    
    # ADX (Average Directional Index)
    'adx': [
        ParameterRange('adx_period', 'int', low=10, high=25, step=1),
        ParameterRange('adx_threshold', 'int', low=15, high=35, step=5),
    ],
    
    # ATR (Average True Range)
    'atr': [
        ParameterRange('atr_period', 'int', low=10, high=20, step=1),
        ParameterRange('atr_sl_mult', 'float', low=1.0, high=3.5, step=0.25),
        ParameterRange('atr_tp_mult', 'float', low=1.5, high=4.0, step=0.25),
        ParameterRange('atr_trail_mult', 'float', low=1.5, high=3.5, step=0.25),
    ],
    
    # Bollinger Bands
    'bollinger': [
        ParameterRange('bb_period', 'int', low=15, high=30, step=5),
        ParameterRange('bb_std', 'float', low=1.5, high=3.0, step=0.25),
    ],
    
    # MACD (Moving Average Convergence Divergence)
    'macd': [
        ParameterRange('macd_fast', 'int', low=8, high=15, step=1),
        ParameterRange('macd_slow', 'int', low=20, high=30, step=2),
        ParameterRange('macd_signal', 'int', low=7, high=12, step=1),
    ],
    
    # Stochastic Oscillator
    'stochastic': [
        ParameterRange('stoch_k_period', 'int', low=10, high=20, step=2),
        ParameterRange('stoch_d_period', 'int', low=3, high=7, step=1),
        ParameterRange('stoch_oversold', 'int', low=15, high=25, step=5),
        ParameterRange('stoch_overbought', 'int', low=75, high=85, step=5),
    ],
    
    # CCI (Commodity Channel Index)
    'cci': [
        ParameterRange('cci_period', 'int', low=15, high=30, step=5),
        ParameterRange('cci_oversold', 'int', low=-120, high=-80, step=10),
        ParameterRange('cci_overbought', 'int', low=80, high=120, step=10),
    ],
    
    # MFI (Money Flow Index)
    'mfi': [
        ParameterRange('mfi_period', 'int', low=10, high=20, step=2),
        ParameterRange('mfi_oversold', 'int', low=15, high=30, step=5),
        ParameterRange('mfi_overbought', 'int', low=70, high=85, step=5),
    ],
    
    # SuperTrend
    'supertrend': [
        ParameterRange('supertrend_period', 'int', low=8, high=15, step=1),
        ParameterRange('supertrend_mult', 'float', low=2.0, high=4.0, step=0.5),
    ],
    
    # Donchian Channels
    'donchian': [
        ParameterRange('donchian_period', 'int', low=15, high=30, step=5),
    ],
    
    # Keltner Channels
    'keltner': [
        ParameterRange('keltner_period', 'int', low=15, high=30, step=5),
        ParameterRange('keltner_mult', 'float', low=1.5, high=3.0, step=0.25),
    ],
    
    # OBV (On-Balance Volume)
    'obv': [
        ParameterRange('obv_smooth_period', 'int', low=10, high=30, step=5),
    ],
    
    # VWAP (Volume Weighted Average Price)
    'vwap': [
        ParameterRange('vwap_deviation', 'float', low=1.0, high=3.0, step=0.5),
    ],
    
    # Generic exit parameters
    'exits': [
        ParameterRange('tp_rr_ratio', 'float', low=1.5, high=4.0, step=0.25),
        ParameterRange('sl_rr_ratio', 'float', low=1.0, high=2.5, step=0.25),
        ParameterRange('breakeven_r', 'float', low=0.5, high=1.5, step=0.25),
        ParameterRange('time_stop_bars', 'int', low=48, high=192, step=24),
    ],
}


if __name__ == '__main__':
    # Example usage
    print("Strategy Optimizer - PROFIT-FIRST Scoring")
    print("="*80)
    
    # Define parameter ranges
    param_ranges = [
        ParameterRange('rsi_period', 'int', low=10, high=20, step=2),
        ParameterRange('rsi_oversold', 'int', low=20, high=35, step=5),
        ParameterRange('adx_threshold', 'int', low=18, high=30, step=2),
        ParameterRange('atr_sl_mult', 'float', low=1.5, high=3.0, step=0.5),
    ]
    
    # Create optimizer
    optimizer = StrategyOptimizer(
        strategy_name='test_strategy',
        param_ranges=param_ranges,
        n_trials=10
    )
    
    # Run optimization
    results = optimizer.optimize(n_jobs=1, sampler='TPE')
    
    print("\n✅ Optimization complete!")
    print(f"Best Score: {results['best_value']:.2f}")
    print(f"Best params: {results['best_params']}")    
    print(f"Best params: {results['best_params']}")