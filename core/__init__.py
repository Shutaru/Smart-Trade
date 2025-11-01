"""
Core Module - Fundamental Building Blocks

Essential utilities used across the system:
- database.py: SQLite database layer
- features.py: Feature calculation
- indicators.py: Technical indicator library
- sizing.py: Position sizing
- metrics.py: Performance metrics
"""

from .database import connect, load_range, insert_candles, insert_features
from .features import compute_feature_rows
from .indicators import supertrend, keltner, rsi, ema, sma, atr, adx
from .sizing import compute_qty
from .metrics import equity_metrics, trades_metrics

__all__ = [
    'connect',
    'load_range',
    'insert_candles',
    'insert_features',
    'compute_feature_rows',
  'supertrend',
    'keltner',
    'rsi',
    'ema',
    'sma',
    'atr',
    'adx',
    'compute_qty',
    'equity_metrics',
    'trades_metrics',
]
