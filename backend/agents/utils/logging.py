"""
Logging utilities for Agent Runner

Features:
- Trajectory JSONL: all events (observations, actions, fills, errors)
- Metrics CSV: equity curve, PnL, drawdown, rolling Sharpe
- Equity JSON: frontend-ready equity curve
"""

import json
import csv
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
import time


class AgentLogger:
    """
    Structured logging for agent runs
    
    Outputs:
    - trajectory.jsonl: All events (one JSON per line)
    - metrics.csv: Equity curve with calculated metrics
    - equity.json: Frontend-ready equity data
    """
    
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        self.trajectory_path = self.run_dir / "trajectory.jsonl"
        self.metrics_path = self.run_dir / "metrics.csv"
        self.equity_path = self.run_dir / "equity.json"
        
        # Metrics buffer for rolling calculations
        self.metrics_buffer: List[Dict[str, float]] = []
        self.rolling_window = 20  # Rolling window for Sharpe
        
        # Initialize metrics CSV
        if not self.metrics_path.exists():
            with open(self.metrics_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'equity',
                    'cash',
                    'realized_pnl',
                    'unrealized_pnl',
                    'total_pnl',
                    'num_positions',
                    'drawdown_pct',
                    'sharpe_rolling',
                    'volatility_rolling'
                ])
        
        print(f"[Logger] Initialized: {self.run_dir}")
    
    def append_event(self, event: dict, kind: str):
        """
        Append event to trajectory JSONL
        
        Args:
            event: Event data (any dict)
            kind: Event type (observation, action, fill, error, etc)
        """
        structured_event = {
            'ts': int(time.time() * 1000),
            'kind': kind,
            'data': event
        }
        
        with open(self.trajectory_path, 'a') as f:
            f.write(json.dumps(structured_event) + '\n')
    
    def log_observation(self, run_id: str, data: dict):
        """Log observation event"""
        self.append_event(data, 'observation')
    
    def log_action(self, run_id: str, data: dict):
        """Log action event"""
        self.append_event(data, 'action')
    
    def log_fill(self, run_id: str, data: dict):
        """Log fill event"""
        self.append_event(data, 'fill')
    
    def log_error(self, run_id: str, error_msg: str, timestamp: int):
        """Log error event"""
        self.append_event({'error': error_msg, 'timestamp': timestamp}, 'error')
    
    def log_event(self, run_id: str, event_type: str, data: dict):
        """Log generic event"""
        self.append_event(data, event_type)
    
    def append_metrics(self, metrics):
        """
        Append metrics to CSV with rolling calculations
        
        Args:
            metrics: Metrics object with equity, cash, pnl, etc
        """
        # Add to buffer
        metrics_dict = {
            'timestamp': metrics.timestamp,
            'equity': metrics.equity,
            'cash': metrics.cash,
            'realized_pnl': metrics.realized_pnl,
            'unrealized_pnl': metrics.unrealized_pnl,
            'total_pnl': metrics.total_pnl,
            'num_positions': metrics.num_positions
        }
        self.metrics_buffer.append(metrics_dict)
        
        # Calculate rolling metrics
        drawdown_pct = self._calculate_drawdown()
        sharpe_rolling = self._calculate_rolling_sharpe()
        volatility_rolling = self._calculate_rolling_volatility()
        
        # Write to CSV
        with open(self.metrics_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                metrics.timestamp,
                metrics.equity,
                metrics.cash,
                metrics.realized_pnl,
                metrics.unrealized_pnl,
                metrics.total_pnl,
                metrics.num_positions,
                drawdown_pct,
                sharpe_rolling,
                volatility_rolling
            ])
        
        # Update equity JSON (frontend-ready)
        self._update_equity_json()
    
    def _calculate_drawdown(self) -> float:
        """
        Calculate current drawdown from peak
        
        Returns:
            Drawdown percentage (negative value)
        """
        if not self.metrics_buffer:
            return 0.0
        
        equities = [m['equity'] for m in self.metrics_buffer]
        peak = max(equities)
        current = equities[-1]
        
        if peak == 0:
            return 0.0
        
        drawdown = ((current - peak) / peak) * 100
        return drawdown
    
    def _calculate_rolling_sharpe(self, risk_free_rate: float = 0.0) -> float:
        """
        Calculate rolling Sharpe ratio
        
        Args:
            risk_free_rate: Annual risk-free rate (default 0%)
        
        Returns:
            Annualized Sharpe ratio
        """
        if len(self.metrics_buffer) < 2:
            return 0.0
        
        # Get recent window
        window = self.metrics_buffer[-min(self.rolling_window, len(self.metrics_buffer)):]
        
        if len(window) < 2:
            return 0.0
        
        # Calculate returns
        equities = [m['equity'] for m in window]
        returns = []
        for i in range(1, len(equities)):
            if equities[i-1] == 0:
                continue
            ret = (equities[i] - equities[i-1]) / equities[i-1]
            returns.append(ret)
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate Sharpe
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assume 2-second intervals → ~15,768,000 intervals/year)
        # Simplified: assume daily data for now
        sharpe = (mean_return - risk_free_rate) / std_return
        sharpe_annualized = sharpe * np.sqrt(252)  # Crypto trades 24/7, use 252 for approximation
        
        return round(sharpe_annualized, 3)
    
    def _calculate_rolling_volatility(self) -> float:
        """
        Calculate rolling volatility (standard deviation of returns)
        
        Returns:
            Annualized volatility percentage
        """
        if len(self.metrics_buffer) < 2:
            return 0.0
        
        # Get recent window
        window = self.metrics_buffer[-min(self.rolling_window, len(self.metrics_buffer)):]
        
        if len(window) < 2:
            return 0.0
        
        # Calculate returns
        equities = [m['equity'] for m in window]
        returns = []
        for i in range(1, len(equities)):
            if equities[i-1] == 0:
                continue
            ret = (equities[i] - equities[i-1]) / equities[i-1]
            returns.append(ret)
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate volatility
        volatility = np.std(returns)
        
        # Annualize
        volatility_annualized = volatility * np.sqrt(252) * 100  # As percentage
        
        return round(volatility_annualized, 2)
    
    def _update_equity_json(self):
        """
        Update equity.json for frontend charts
        
        Format:
        [
            {"ts": 1737399000000, "equity": 10000.0, "drawdown": 0.0},
            {"ts": 1737399002000, "equity": 10020.5, "drawdown": -0.5},
            ...
        ]
        """
        if not self.metrics_buffer:
            return
        
        # Calculate drawdown for each point
        equities = [m['equity'] for m in self.metrics_buffer]
        timestamps = [m['timestamp'] for m in self.metrics_buffer]
        
        peak = equities[0]
        equity_data = []
        
        for i, (ts, equity) in enumerate(zip(timestamps, equities)):
            # Update peak
            if equity > peak:
                peak = equity
            
            # Calculate drawdown
            drawdown = ((equity - peak) / peak) * 100 if peak > 0 else 0.0
            
            equity_data.append({
                'ts': ts,
                'equity': round(equity, 2),
                'drawdown': round(drawdown, 2)
            })
        
        # Write to JSON
        with open(self.equity_path, 'w') as f:
            json.dump(equity_data, f, indent=2)
    
    def write_summary(self, summary: Dict[str, Any]):
        """
        Write run summary JSON
        
        Args:
            summary: Summary dict with final metrics, risk stats, etc
        """
        summary_path = self.run_dir / "summary.json"
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"[Logger] Summary saved: {summary_path}")
    
    def get_metrics_dataframe(self) -> pd.DataFrame:
        """
        Load metrics CSV as DataFrame
        
        Returns:
            DataFrame with all metrics
        """
        if not self.metrics_path.exists():
            return pd.DataFrame()
        
        return pd.read_csv(self.metrics_path)
    
    def get_equity_data(self) -> List[Dict[str, float]]:
        """
        Load equity JSON
        
        Returns:
            List of equity data points
        """
        if not self.equity_path.exists():
            return []
        
        with open(self.equity_path, 'r') as f:
            return json.load(f)