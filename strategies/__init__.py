"""
Strategies Module - 38 Professional Trading Strategies

This module contains the complete strategy system with:
- 5 Trend Following strategies
- 5 Mean Reversion strategies
- 5 Breakout strategies
- 5 Volume-based strategies
- 5 Hybrid strategies
- 5 Advanced strategies
- 5 Refinement strategies
- 3 Final strategies

Total: 38 strategies across 8 categories
"""

from .registry import (
    get_strategy,
    list_all_strategies,
    get_strategies_by_category,
    get_strategy_info,
    ALL_STRATEGIES,
    STRATEGY_PRESETS
)

from .core import compute_exit_levels
from .regime import build_regime_exit_plan
from .adapter import (
    build_indicator_dict,
    build_bar_dict,
build_state_dict,
extract_exit_params
)

__all__ = [
    'get_strategy',
    'list_all_strategies',
    'get_strategies_by_category',
    'get_strategy_info',
    'ALL_STRATEGIES',
'STRATEGY_PRESETS',
    'compute_exit_levels',
    'build_regime_exit_plan',
    'build_indicator_dict',
    'build_bar_dict',
    'build_state_dict',
    'extract_exit_params',
]
