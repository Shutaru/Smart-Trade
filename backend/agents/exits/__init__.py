"""
Regime-Adaptive Exit System

Professional exit management with:
- Structure-aware stop losses
- Multi-target partial exits
- Breakeven automation
- Trailing stops (ATR, Chandelier, Keltner, SuperTrend)
- Regime-adaptive parameters
"""

from .regime_exit_plan import (
    ExitPlan,
    Target,
    Trailing,
    Side,
    TrailMode,
    RegimeHint,
    build_exit_plan,
    update_trailing_stop,
    check_exits
)

from .regime_detector import (
    RegimeDetector,
    RegimeType,
    get_swing_levels,
    build_context
)

__all__ = [
    # Exit plan
    "ExitPlan",
    "Target",
    "Trailing",
    "Side",
    "TrailMode",
    "RegimeHint",
    "build_exit_plan",
    "update_trailing_stop",
    "check_exits",
    
    # Regime detection
    "RegimeDetector",
    "RegimeType",
    "get_swing_levels",
    "build_context"
]
