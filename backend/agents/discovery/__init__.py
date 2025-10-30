"""
Strategy Discovery Engine

Automatically discovers and ranks trading strategies using:
- All available indicators (RSI, MACD, EMA, SMA, ADX, ATR, BB, SuperTrend, etc.)
- LLM-guided indicator combinations
- Advanced ranking formula (Calmar, Sortino, Stability)
"""

from .strategy_catalog import StrategyCatalog
from .discovery_engine import StrategyDiscoveryEngine
from .ranker import StrategyRanker

__all__ = ['StrategyCatalog', 'StrategyDiscoveryEngine', 'StrategyRanker']
