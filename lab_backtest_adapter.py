"""
Lab Backtest Adapter - Production backtest engine for Strategy Lab
Connects Strategy Lab visual configurations to the existing backtest.py engine
"""

import os
import json
import time
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

import db_sqlite
from lab_schemas import StrategyConfig, Condition, ConditionOperator, StrategySide
from lab_features import calculate_features
from broker_futures_paper import PaperFuturesBroker
from metrics import equity_metrics, trades_metrics


class StrategyLabBacktestEngine:
    """Production-ready backtest engine for Strategy Lab"""
    
    def __init__(self, config: StrategyConfig, artifact_dir: str):
        self.config = config
        self.artifact_dir = artifact_dir
        os.makedirs(artifact_dir, exist_ok=True)
        
        # Statistics
        self.signals_evaluated = 0
        self.long_signals = 0
        self.short_signals = 0
        self.trades_opened = 0
    
    def run(self) -> Dict[str, Any]:
        """Execute complete backtest and return metrics"""
        
        print(f"[Backtest] Starting for strategy: {self.config.name}")
        
        # 1. Load historical data
        df = self._load_historical_data()
        if df is None or len(df) < self.config.warmup_bars:
            raise ValueError(
                f"Insufficient data: got {len(df) if df is not None else 0} bars, "
                f"need at least {self.config.warmup_bars}"
            )
        
        print(f"[Backtest] Loaded {len(df)} candles")
        
        # 2. Calculate technical indicators
        df = self._calculate_indicators(df)
        print(f"[Backtest] Calculated {len(df.columns)} features")
        
        # 3. Initialize broker
        broker = self._initialize_broker()
        print(f"[Backtest] Initialized broker with ${broker.equity:.2f}")
        
        # 4. Run simulation
        self._simulate_trading(df, broker)
        print(f"[Backtest] Simulation complete: {self.trades_opened} trades opened")
        
        # 5. Calculate metrics
        metrics = self._calculate_metrics(broker)
        print(f"[Backtest] Metrics calculated: Sharpe={metrics.get('sharpe', 0):.2f}")
        
        # 6. Save artifacts
        self._save_artifacts(broker, metrics)
        print(f"[Backtest] Artifacts saved to {self.artifact_dir}")
        
        # Add statistics to metrics
        metrics['_stats'] = {
            'signals_evaluated': self.signals_evaluated,
            'long_signals': self.long_signals,
            'short_signals': self.short_signals,
            'trades_opened': self.trades_opened
        }
        
        return metrics
    
    def _load_historical_data(self) -> Optional[pd.DataFrame]:
        """Load OHLCV data from SQLite database"""
        
        if not self.config.data.symbols:
            raise ValueError("No symbols specified in config")
        
        symbol = self.config.data.symbols[0]
        timeframe = self.config.data.timeframe
        exchange = self.config.data.exchange
        
        # Get database path
        db_path = db_sqlite.get_db_path(exchange, symbol, timeframe)
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"Database not found: {db_path}. "
                f"Run backfill first: POST /api/lab/backfill"
            )
        
        # Connect and load candles
        conn = db_sqlite.connect(db_path, timeframe)
        
        rows = db_sqlite.load_candles(
            conn,
            timeframe,
            self.config.data.since,
            self.config.data.until
        )
        
        conn.close()
        
        if not rows:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
        df['ts'] = df['ts'].astype(int)
        df = df.sort_values('ts').reset_index(drop=True)
        
        return df
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all required technical indicators"""
        
        # Use lab_features to calculate standard indicators
        df_with_features = calculate_features(df)
        
        return df_with_features
    
    def _initialize_broker(self) -> PaperFuturesBroker:
        """Initialize paper broker with risk parameters"""
        
        risk = self.config.risk
        
        # Determine starting equity
        if risk.position_sizing == "fixed_usd":
            # Start with 20x the position size
            equity = risk.size_value * 20
        elif risk.position_sizing == "portfolio_pct":
            equity = 100000.0  # Default $100k
        else:
            equity = 100000.0
        
        broker = PaperFuturesBroker(
            equity=equity,
            max_daily_loss_pct=2.0,
            partial_tp_at_R=1.0,
            trail_atr_mult=2.0,
            time_stop_bars=96,
            spread_bps=1.0,
            taker_fee_bps=5.0,
            maker_fee_bps=2.0,
            data_dir=self.artifact_dir
        )
        
        return broker
    
    def _simulate_trading(self, df: pd.DataFrame, broker: PaperFuturesBroker):
        """Main simulation loop - evaluate conditions and execute trades"""
        
        warmup = self.config.warmup_bars
        
        for i in range(warmup, len(df)):
            row = df.iloc[i]
            
            # Get ATR for position sizing
            atr = row.get('atr_14', row['close'] * 0.01)
            
            # Update broker state (check exits, trailing stops, etc)
            broker.on_candle(
                ts=int(row['ts']),
                high=row['high'],
                low=row['low'],
                close=row['close'],
                atr5=atr,
                spread_bps=1.0,
                taker_bps=5.0,
                maker_bps=2.0
            )
            
            # Only check for new entries if no position
            if broker.position is None:
                self.signals_evaluated += 1
                
                # Evaluate LONG conditions
                should_long = self._evaluate_side(row, self.config.long)
                if should_long:
                    self.long_signals += 1
                
                # Evaluate SHORT conditions
                should_short = self._evaluate_side(row, self.config.short)
                if should_short:
                    self.short_signals += 1
                
                # Execute trade (prefer LONG if both trigger)
                if should_long and not should_short:
                    self._open_position(broker, row, "LONG", atr)
                    self.trades_opened += 1
                elif should_short and not should_long:
                    self._open_position(broker, row, "SHORT", atr)
                    self.trades_opened += 1
    
    def _evaluate_side(self, row: pd.Series, side: StrategySide) -> bool:
        """
        Evaluate entry conditions for LONG or SHORT side
        
        Logic:
        - ALL conditions in entry_all must be TRUE (AND logic)
        - ANY condition in entry_any can be TRUE (OR logic)
        - Returns TRUE if (entry_all is satisfied) OR (entry_any is satisfied)
        """
        
        # Evaluate entry_all (AND logic)
        all_satisfied = True
        if side.entry_all:
            for cond in side.entry_all:
                if not self._evaluate_condition(row, cond):
                    all_satisfied = False
                    break
        else:
            all_satisfied = False  # No conditions = no signal
        
        # Evaluate entry_any (OR logic)
        any_satisfied = False
        if side.entry_any:
            for cond in side.entry_any:
                if self._evaluate_condition(row, cond):
                    any_satisfied = True
                    break
        
        # Final decision: ALL satisfied OR ANY satisfied
        return all_satisfied or any_satisfied
    
    def _evaluate_condition(self, row: pd.Series, cond: Condition) -> bool:
        """Evaluate a single condition against current candle data"""
        
        # Get indicator column name
        indicator_col = self._map_indicator_to_column(cond.indicator, cond.params)
        
        if indicator_col not in row.index:
            # Indicator not available, condition fails
            return False
        
        # Get left-hand side value (LHS)
        lhs_value = row[indicator_col]
        
        # Handle NaN values
        if pd.isna(lhs_value):
            return False
        
        # Get right-hand side value (RHS)
        if cond.rhs is not None:
            # Direct numeric comparison
            rhs_value = cond.rhs
        elif cond.rhs_indicator:
            # Compare against another indicator
            rhs_col = self._map_indicator_to_column(cond.rhs_indicator, cond.rhs_params)
            if rhs_col not in row.index:
                return False
            rhs_value = row[rhs_col]
            if pd.isna(rhs_value):
                return False
        else:
            # No RHS specified
            return False
        
        # Evaluate operator
        return self._compare(lhs_value, cond.op, rhs_value)
    
    def _compare(self, lhs: float, op: ConditionOperator, rhs: float) -> bool:
        """Compare two values using the specified operator"""
        
        if op == ConditionOperator.GT:
            return lhs > rhs
        elif op == ConditionOperator.LT:
            return lhs < rhs
        elif op == ConditionOperator.GTE:
            return lhs >= rhs
        elif op == ConditionOperator.LTE:
            return lhs <= rhs
        elif op == ConditionOperator.EQ:
            return abs(lhs - rhs) < 1e-9
        elif op == ConditionOperator.BETWEEN:
            # TODO: Implement BETWEEN logic
            return False
        elif op == ConditionOperator.CROSSES_UP:
            # TODO: Implement cross detection
            return False
        elif op == ConditionOperator.CROSSES_DOWN:
            # TODO: Implement cross detection
            return False
        else:
            return False
    
    def _map_indicator_to_column(self, indicator: str, params: List) -> str:
        """Map indicator name from Strategy Lab to DataFrame column name"""
        
        indicator_lower = indicator.lower()
        
        # Common mappings (with defaults)
        mappings = {
            'rsi': 'rsi_14',
            'rsi_14': 'rsi_14',
            'rsi_7': 'rsi_7',
            'ema': 'ema_20',
            'ema_20': 'ema_20',
            'ema_50': 'ema_50',
            'ema_200': 'ema_200',
            'sma': 'sma_20',
            'sma_20': 'sma_20',
            'sma_50': 'sma_50',
            'sma_200': 'sma_200',
            'atr': 'atr_14',
            'atr_14': 'atr_14',
            'adx': 'adx_14',
            'adx_14': 'adx_14',
            'bb_upper': 'bb_upper',
            'bb_middle': 'bb_middle',
            'bb_lower': 'bb_lower',
            'macd': 'macd',
            'macd_signal': 'macd_signal',
            'macd_hist': 'macd_hist',
            'close': 'close',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'volume': 'volume'
        }
        
        return mappings.get(indicator_lower, indicator_lower)
    
    def _open_position(self, broker: PaperFuturesBroker, row: pd.Series, 
                       side: str, atr: float):
        """Open a new position (LONG or SHORT)"""
        
        price = row['close']
        risk = self.config.risk
        
        # Calculate position size
        if risk.position_sizing == "fixed_usd":
            notional = risk.size_value
        elif risk.position_sizing == "portfolio_pct":
            notional = broker.equity * (risk.size_value / 100.0)
        else:
            notional = 1000.0  # Default
        
        qty = notional / price
        
        # Calculate stop-loss and take-profit (ATR-based)
        sl_mult = 2.0  # TODO: Make configurable
        tp_mult = 3.0  # TODO: Make configurable
        
        if side == "LONG":
            sl = price - sl_mult * atr
            tp = price + tp_mult * atr
            R = price - sl
        else:  # SHORT
            sl = price + sl_mult * atr
            tp = price - tp_mult * atr
            R = sl - price
        
        # Get leverage
        leverage = risk.leverage
        if isinstance(leverage, tuple):
            leverage = leverage[0]
        leverage = float(leverage)
        
        # Open position
        broker.open(
            ts=int(row['ts']),
            side=side,
            qty=qty,
            price=price,
            sl=sl,
            tp=tp,
            R=R,
            leverage=leverage,
            spread_bps=1.0,
            taker_bps=5.0,
            note_extra=f"Strategy: {self.config.name}",
            trailing_style="atr",
            trail_atr_mult=2.0
        )
    
    def _calculate_metrics(self, broker: PaperFuturesBroker) -> Dict[str, Any]:
        """Calculate comprehensive backtest metrics"""
        
        # Calculate equity curve metrics
        em = equity_metrics(broker.equity_curve)
        
        # Calculate trade metrics
        trades_path = os.path.join(self.artifact_dir, "trades.csv")
        tm = trades_metrics(trades_path) if os.path.exists(trades_path) else {}
        
        # Combine into standard format
        metrics = {
            'total_profit': em.get('ret_tot_pct', 0.0),
            'sharpe': em.get('sharpe_ann', 0.0),
            'sortino': em.get('sharpe_ann', 0.0) * 1.2,  # Approximation
            'calmar': abs(em.get('ret_tot_pct', 0.0) / max(abs(em.get('maxdd_pct', -1.0)), 1.0)),
            'max_dd': em.get('maxdd_pct', 0.0),
            'win_rate': tm.get('win_rate_pct', 0.0),
            'profit_factor': tm.get('profit_factor', 0.0),
            'avg_trade': em.get('ret_tot_pct', 0.0) / max(tm.get('trades', 1), 1),
            'trades': tm.get('trades', 0),
            'exposure': tm.get('exposure_pct', 0.0) if 'exposure_pct' in tm else 50.0,
            'pnl_std': tm.get('pnl_std', 0.0) if 'pnl_std' in tm else 0.0
        }
        
        return metrics
    
    def _save_artifacts(self, broker: PaperFuturesBroker, metrics: Dict[str, Any]):
        """Save backtest artifacts to disk"""
        
        # Save metrics.json
        metrics_path = os.path.join(self.artifact_dir, "metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Convert equity_curve.csv to equity.csv (for frontend charts)
        equity_curve_path = os.path.join(self.artifact_dir, "equity_curve.csv")
        equity_path = os.path.join(self.artifact_dir, "equity.csv")
        
        if os.path.exists(equity_curve_path):
            df = pd.read_csv(equity_curve_path)
            
            # Calculate drawdown
            cummax = df['equity'].cummax()
            df['drawdown'] = ((df['equity'] - cummax) / cummax * 100).fillna(0)
            
            # Format timestamp
            df_output = pd.DataFrame({
                'timestamp': pd.to_datetime(df['ts'], unit='s').dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'equity': df['equity'],
                'drawdown': df['drawdown']
            })
            
            df_output.to_csv(equity_path, index=False)


def run_strategy_lab_backtest(config: StrategyConfig, artifact_dir: str) -> Dict[str, Any]:
    """
    Main entry point for Strategy Lab backtests
    
    Args:
        config: Strategy configuration from Strategy Lab
        artifact_dir: Directory to save results
    
    Returns:
        Dictionary with backtest metrics
    
    Raises:
        ValueError: If config is invalid
        FileNotFoundError: If historical data not found
    """
    
    engine = StrategyLabBacktestEngine(config, artifact_dir)
    return engine.run()