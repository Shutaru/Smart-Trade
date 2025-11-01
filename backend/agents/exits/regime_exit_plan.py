"""
Regime-Adaptive Exit Plan System

Features:
- Structure-aware SL (swing low/high + ATR buffer)
- Multi-target exits (partial TP at multiple R levels)
- Breakeven automation
- Trailing stops (ATR, Chandelier, Keltner, SuperTrend)
- Regime-adaptive parameters (trend, range, high_vol, low_vol)
- Time stops
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any

Side = Literal["LONG", "SHORT"]
TrailMode = Literal["none", "atr", "chandelier", "supertrend", "keltner"]
RegimeHint = Optional[Literal["trend", "range", "high_vol", "low_vol"]]


@dataclass
class Target:
    """Partial exit target"""
    rr: float           # Risk multiples (e.g., 1.0 = 1R)
    pct: float          # % of position to close (0-1)
    price: float        # Actual price level


@dataclass
class Trailing:
    """Trailing stop configuration"""
    mode: TrailMode = "none"
    atr_mult: float = 2.0
    breakeven_at_R: Optional[float] = None
    keltner_mult: float = 1.5
    offset: float = 0.0


@dataclass
class ExitPlan:
    """Complete exit plan for a position"""
    side: Side
    entry: float
    sl: float
    tp_primary: float
    R: float
    targets: List[Target] = field(default_factory=list)
    trailing: Trailing = field(default_factory=Trailing)
    time_stop_bars: Optional[int] = None
    cooldown_bars: int = 0
    
    # Runtime tracking
    bars_in_trade: int = 0
    breakeven_done: bool = False
    targets_hit: List[int] = field(default_factory=list)


def _round_to_tick(px: float, tick: Optional[float], up: bool) -> float:
    """Round price to tick size"""
    if not tick or tick == 0:
        return px
    k = int(px / tick + (1 if up else 0))
    return k * tick


def _swing_buffer(ctx: Dict[str, Any], atr: float, mult: float = 0.2) -> float:
    """Add small buffer around swing using ATR fraction"""
    return max(ctx.get("tick_size", 0.0), atr * mult)


def build_exit_plan(
    side: Side,
    entry: float,
    atr: float,
    params: Dict[str, Any],
    ctx: Optional[Dict[str, Any]] = None,
    regime_hint: RegimeHint = None,
) -> ExitPlan:
    """
    Build regime-adaptive exit plan with multi-targets and trailing
    
    Args:
        side: LONG or SHORT
        entry: Entry price
        atr: Current ATR value
        params: Strategy parameters from config
        ctx: Market context (swings, indicators, tick size)
        regime_hint: Market regime (trend, range, high_vol, low_vol)
    
    Returns:
        ExitPlan with SL, TP, targets, and trailing config
    """
    ctx = ctx or {}
    tick = ctx.get("tick_size", 0.01)
    
    # === Defaults ===
    style = params.get("sl_tp_style", "structure_atr")
    sl_mult = float(params.get("sl_atr_mult", 2.2))
    trail_mult = float(params.get("trail_atr_mult", 2.0))
    
    # Default targets: 35% @ 1R, 35% @ 2R, 30% runner
    default_targets = params.get("targets", [
        {"rr": 1.0, "pct": 0.35},
        {"rr": 2.0, "pct": 0.35},
        {"rr": 3.0, "pct": 0.30}
    ])
    
    # === Regime Adjustments ===
    if regime_hint == "trend":
        sl_mult *= 1.1
        default_targets = [
            {"rr": 1.0, "pct": 0.25},
            {"rr": 2.5, "pct": 0.35},
            {"rr": 4.0, "pct": 0.40}
        ]
    elif regime_hint == "range":
        sl_mult *= 0.9
        default_targets = [
            {"rr": 0.8, "pct": 0.40},
            {"rr": 1.6, "pct": 0.40},
            {"rr": 2.5, "pct": 0.20}
        ]
    elif regime_hint == "high_vol":
        sl_mult *= 1.2
        default_targets = [
            {"rr": 0.8, "pct": 0.40},
            {"rr": 1.6, "pct": 0.40},
            {"rr": 2.2, "pct": 0.20}
        ]
    elif regime_hint == "low_vol":
        sl_mult *= 0.95
    
    # === Initial SL (structure + ATR) ===
    if side == "LONG":
        if style in ("structure_atr", "chandelier", "keltner", "supertrend"):
            swing_low = ctx.get("swing_low", entry - sl_mult * atr)
            base_sl = min(swing_low, entry - sl_mult * atr)
            base_sl = base_sl - _swing_buffer(ctx, atr)
        else:
            base_sl = entry - sl_mult * atr
        
        base_sl = _round_to_tick(base_sl, tick, up=False)
        R = entry - base_sl
        tp_primary = entry + params.get("tp_rr_multiple", 2.0) * R
    
    else:  # SHORT
        if style in ("structure_atr", "chandelier", "keltner", "supertrend"):
            swing_high = ctx.get("swing_high", entry + sl_mult * atr)
            base_sl = max(swing_high, entry + sl_mult * atr)
            base_sl = base_sl + _swing_buffer(ctx, atr)
        else:
            base_sl = entry + sl_mult * atr
        
        base_sl = _round_to_tick(base_sl, tick, up=True)
        R = base_sl - entry
        tp_primary = entry - params.get("tp_rr_multiple", 2.0) * R
    
    # === Build targets ===
    targets: List[Target] = []
    for t in default_targets:
        rr = float(t["rr"])
        if side == "LONG":
            price = _round_to_tick(entry + rr * R, tick, up=True)
        else:
            price = _round_to_tick(entry - rr * R, tick, up=False)
        targets.append(Target(rr=rr, pct=float(t["pct"]), price=price))
    
    # === Trailing config ===
    tmode: TrailMode = "none"
    if style == "atr_trailing":
        tmode = "atr"
    elif style == "chandelier":
        tmode = "chandelier"
    elif style == "supertrend":
        tmode = "supertrend"
    elif style == "keltner":
        tmode = "keltner"
    
    trailing = Trailing(
        mode=tmode,
        atr_mult=trail_mult,
        breakeven_at_R=float(params.get("breakeven_at_R", 1.0)),
        keltner_mult=float(params.get("keltner_mult", 1.5)),
        offset=float(params.get("trail_offset", 0.0)),
    )
    
    # === Time stop (regime-adaptive) ===
    time_stop_bars = params.get("time_stop_bars", 96)
    if regime_hint == "high_vol":
        time_stop_bars = int(time_stop_bars * 0.75)
    elif regime_hint == "low_vol":
        time_stop_bars = int(time_stop_bars * 1.25)
    
    cooldown_bars = params.get("cooldown_bars", 0)
    
    return ExitPlan(
        side=side,
        entry=entry,
        sl=base_sl,
        tp_primary=tp_primary,
        R=R,
        targets=targets,
        trailing=trailing,
        time_stop_bars=time_stop_bars,
        cooldown_bars=cooldown_bars
    )


def update_trailing_stop(
    plan: ExitPlan,
    last: Dict[str, float],
    ctx: Dict[str, Any],
    atr: float
):
    """
    Update trailing stop based on current bar
    
    Args:
        plan: ExitPlan to update
        last: Current bar data (high, low, close, highest_since_entry, lowest_since_entry)
        ctx: Market context (tick_size, supertrend, keltner channels)
        atr: Current ATR
    """
    tick = ctx.get("tick_size", 0.01)
    mode = plan.trailing.mode
    side = plan.side
    
    # === Breakeven trigger ===
    if plan.trailing.breakeven_at_R and not plan.breakeven_done:
        profit_R = 0.0
        if side == "LONG":
            profit_R = (last["close"] - plan.entry) / plan.R if plan.R > 0 else 0
        else:
            profit_R = (plan.entry - last["close"]) / plan.R if plan.R > 0 else 0
        
        if profit_R >= plan.trailing.breakeven_at_R:
            if side == "LONG":
                plan.sl = max(plan.sl, _round_to_tick(plan.entry, tick, up=False))
            else:
                plan.sl = min(plan.sl, _round_to_tick(plan.entry, tick, up=True))
            plan.breakeven_done = True
    
    if mode == "none":
        return
    
    # === Calculate new trailing level ===
    if side == "LONG":
        if mode == "atr":
            trail = last["highest_since_entry"] - plan.trailing.atr_mult * atr
        elif mode == "chandelier":
            trail = last["highest_since_entry"] - plan.trailing.atr_mult * atr
        elif mode == "supertrend":
            st = ctx.get("supertrend")
            if st is None:
                return
            trail = st - plan.trailing.offset
        elif mode == "keltner":
            kel_lo = ctx.get("keltner_lo")
            if kel_lo is None:
                return
            trail = kel_lo - plan.trailing.atr_mult * 0.5 * atr
        else:
            return
        
        plan.sl = max(plan.sl, _round_to_tick(trail, tick, up=False))
    
    else:  # SHORT
        if mode == "atr":
            trail = last["lowest_since_entry"] + plan.trailing.atr_mult * atr
        elif mode == "chandelier":
            trail = last["lowest_since_entry"] + plan.trailing.atr_mult * atr
        elif mode == "supertrend":
            st = ctx.get("supertrend")
            if st is None:
                return
            trail = st + plan.trailing.offset
        elif mode == "keltner":
            kel_up = ctx.get("keltner_up")
            if kel_up is None:
                return
            trail = kel_up + plan.trailing.atr_mult * 0.5 * atr
        else:
            return
        
        plan.sl = min(plan.sl, _round_to_tick(trail, tick, up=True))


def check_exits(
    plan: ExitPlan,
    current_price: float,
    high: float,
    low: float
) -> Optional[tuple[str, float, Optional[float]]]:
    """
    Check if any exit condition is hit
    
    Returns:
        (exit_reason, exit_price, partial_pct) or None
    """
    
    # Check time stop
    if plan.time_stop_bars and plan.bars_in_trade >= plan.time_stop_bars:
        return ("TIME_STOP", current_price, None)
    
    # Check targets (partial exits)
    for i, target in enumerate(plan.targets):
        if i in plan.targets_hit:
            continue
        
        if plan.side == "LONG":
            if high >= target.price:
                plan.targets_hit.append(i)
                return (f"TARGET_{i+1}", target.price, target.pct)
        else:
            if low <= target.price:
                plan.targets_hit.append(i)
                return (f"TARGET_{i+1}", target.price, target.pct)
    
    # Check SL
    if plan.side == "LONG":
        if low <= plan.sl:
            return ("STOP", plan.sl, None)
    else:
        if high >= plan.sl:
            return ("STOP", plan.sl, None)
    
    # Check primary TP
    if plan.side == "LONG":
        if high >= plan.tp_primary:
            return ("TP_FULL", plan.tp_primary, None)
    else:
        if low <= plan.tp_primary:
            return ("TP_FULL", plan.tp_primary, None)
    
    return None