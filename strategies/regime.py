"""
Strategy with Regime-Adaptive Exit System

Integrates:
- Regime detection (ADX, ATR, BB squeeze)
- Structure-aware entries
- Multi-target exits
- Trailing stops adapted to regime
"""

import sys
sys.path.append('.')

from typing import Dict, Any, List, Optional
from backend.agents.exits import (
    build_exit_plan,
    ExitPlan,
    RegimeDetector,
    get_swing_levels,
    build_context as build_exit_context
)


def detect_regime(
    i: int,
    feats: Dict[str, List[float]],
    lookback: int = 100
) -> str:
    """
    Detect market regime at current bar
    
    Returns: "trend", "range", "high_vol", or "low_vol"
    """
    if i < lookback:
        return "range"  # Default for early bars
    
    detector = RegimeDetector(lookback_bars=lookback)
    
    try:
        regime = detector.detect_simple(
            adx_current=feats['adx14'][i],
            atr_current=feats['atr14'][i],
            atr_history=feats['atr14'][max(0, i-lookback):i+1],
            close_current=feats['ema20'][i],  # Using close proxy
            ema200_current=feats.get('ema200', [None])[i] if 'ema200' in feats else None
        )
        return regime
    except (KeyError, IndexError, TypeError):
        return "range"


def should_enter_with_regime(
    i: int,
    ts: List[int],
    o: List[float],
    h: List[float],
    l: List[float],
    c: List[float],
    feats: Dict[str, List[float]],
    params: Dict[str, Any],
    allow_shorts: bool = True
) -> Optional[str]:
    """
    Entry decision with regime awareness
    
    Returns: "LONG", "SHORT", or None
    """
    if i < 1:
        return None
    
    try:
        # Get indicators
        obv = feats['obv'][i]
        obv_prev = feats['obv'][i-1]
        
        dn55 = feats['dn55'][i]
        up55 = feats['up55'][i]
        rsi14 = feats['rsi14'][i]
        
        price = c[i]
        range_size = up55 - dn55
        
        # Detect regime
        regime = detect_regime(i, feats)
        
        # LONG: OBV crosses above 0, price near bottom
        obv_cross_up = obv_prev < 0 and obv >= 0
        near_bottom = (price - dn55) < (range_size * 0.3)
        not_overbought = rsi14 < 50
        
        # In TREND regime, be more aggressive
        if regime == "trend":
            not_overbought = rsi14 < 60
        
        if obv_cross_up and near_bottom and not_overbought:
            return 'LONG'
        
        # SHORT: OBV crosses below 0, price near top
        if not allow_shorts:
            return None
        
        obv_cross_down = obv_prev > 0 and obv <= 0
        near_top = (up55 - price) < (range_size * 0.3)
        not_oversold = rsi14 > 50
        
        # In TREND regime, be more aggressive
        if regime == "trend":
            not_oversold = rsi14 > 40
        
        if obv_cross_down and near_top and not_oversold:
            return 'SHORT'
    
    except (KeyError, IndexError, TypeError):
        pass
    
    return None


def build_regime_exit_plan(
    side: str,
    entry: float,
    atr: float,
    i: int,
    h: List[float],
    l: List[float],
    feats: Dict[str, List[float]],
    params: Dict[str, Any]
) -> ExitPlan:
    """
    Build exit plan with regime detection and structure awareness
    
    Args:
        side: LONG or SHORT
        entry: Entry price
        atr: Current ATR
        i: Current bar index
        h: High prices
        l: Low prices
        feats: Features dict
        params: Strategy parameters
    
    Returns:
        ExitPlan with regime-adaptive parameters
    """
    
    # Detect regime
    regime = detect_regime(i, feats)
    
    # Get swing levels
    swing_low, swing_high = get_swing_levels(h, l, lookback=20, current_idx=i)
    
    # Build context
    ctx = {
        "tick_size": 0.1,  # BTC default
        "swing_low": swing_low,
        "swing_high": swing_high,
        "keltner_lo": feats.get('keltner_lo', [None])[i],
        "keltner_up": feats.get('keltner_up', [None])[i],
        "supertrend": feats.get('supertrend', [None])[i]
    }
    
    # Build exit plan
    plan = build_exit_plan(
        side=side,
        entry=entry,
        atr=atr,
        params=params,
        ctx=ctx,
        regime_hint=regime
    )
    
    return plan


def compute_exit_levels_regime(
    side: str,
    price: float,
    atr: float,
    params: Dict[str, Any],
    i: int = -1,
    h: Optional[List[float]] = None,
    l: Optional[List[float]] = None,
    feats: Optional[Dict[str, List[float]]] = None,
    regime_hint: Optional[str] = None
):
    """
    Backwards-compatible wrapper for legacy code
    
    Returns: (sl, tp, extra_dict)
    """
    
    # If we have full context, use regime system
    if h and l and feats and i >= 0:
        plan = build_regime_exit_plan(side, price, atr, i, h, l, feats, params)
        
        extra = {
            "exit_plan": plan,
            "trail_atr_mult": plan.trailing.atr_mult,
            "breakeven_at_R": plan.trailing.breakeven_at_R
        }
        
        return plan.sl, plan.tp_primary, extra
    
    # Fallback to simple calculation
    sl_mult = float(params.get("sl_atr_mult", 2.2))
    tp_rr = float(params.get("tp_rr_multiple", 2.0))
    
    if side == "LONG":
        sl = price - sl_mult * atr
        R = price - sl
        tp = price + tp_rr * R
    else:
        sl = price + sl_mult * atr
        R = sl - price
        tp = price - tp_rr * R
    
    extra = {
        "trail_atr_mult": float(params.get("trail_atr_mult", 2.0)),
        "breakeven_at_R": float(params.get("breakeven_at_R", 1.0))
    }
    
    return sl, tp, extra