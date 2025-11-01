"""
Strategy Discovery Engine

Automatically discovers and ranks trading strategies using:
- All available indicators (RSI, MACD, EMA, SMA, ADX, ATR, BB, SuperTrend, etc.)
- LLM-guided indicator combinations
- Advanced ranking formula (Calmar, Sortino, Stability)
"""

from .strategy_catalog from strategies import core as strategyCatalog
from .discovery_engine from strategies import core as strategyDiscoveryEngine
from .ranker from strategies import core as strategyRanker

__all__ = ['StrategyCatalog', 'StrategyDiscoveryEngine', 'StrategyRanker']
