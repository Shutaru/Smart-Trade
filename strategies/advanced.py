"""
Advanced & Session-Based Strategies (26-30)

Implementation of advanced strategies with:
- London breakout with ATR filtering
- NY session fade (high vol mean reversion)
- Regime-adaptive core (auto strategy selection)
- Pure price action with Donchian
- Order flow momentum with VWAP

Regime: session_breakout, high_vol->mean, auto, trend, momentum
"""

from typing import Optional, Dict, Any


def london_breakout_atr_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: London Breakout ATR
    Category: Session / Breakout
    
    LONG: London ORB window + ATR above median + close > Opening Range High
    SHORT: close < Opening Range Low
    Exits: atr_trailing, sl=2.2, trail=2.4, tp=2.2
    
    Note: Requires session detection and ORB calculation
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # Session detection (simplified: check if in London hours)
    # Assuming 'session' indicator or timestamp analysis
    is_london_session = ind.get('is_london_session', False)
    
    # Opening Range High/Low (calculated from first N bars of session)
    or_high = ind.get('or_high', float('inf'))
    or_low = ind.get('or_low', 0)
    
    # ATR filter
    atr_norm_pct = ind.get('atr_norm_pct', 50)
    atr_above_median = atr_norm_pct >= 50
    
    # LONG: Break above Opening Range High
    if is_london_session and atr_above_median and close > or_high:
        return {
            "side": "LONG",
            "reason": f"London ORB breakout (ATR pct={atr_norm_pct:.1f}, close>{or_high:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 2.2,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.4,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Break below Opening Range Low
    if is_london_session and atr_above_median and close < or_low:
        return {
            "side": "SHORT",
            "reason": f"London ORB breakdown (ATR pct={atr_norm_pct:.1f}, close<{or_low:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 2.2,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.4,
                "breakeven_at_R": None
            }
        }
    
    return None


def ny_session_fade_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: NY Session Fade
    Category: Session / Mean Reversion
    
    LONG: After NY open, spike below keltner_lower/BB_lower + RSI 25-35 + trigger up
    SHORT: spike above keltner_upper + RSI 65-75 + trigger down
    Exits: breakeven_then_trail, sl=1.7, tp=1.8, be=0.8
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    low = bar['low']
    high = bar['high']
    
    # Session detection
    is_ny_session = ind.get('is_ny_session', False)
    minutes_since_ny_open = ind.get('minutes_since_ny_open', 999)
    
    # Only trade within first 2 hours of NY open
    if not is_ny_session or minutes_since_ny_open > 120:
        return None
    
    keltner_lower = ind.get('keltner_lower', 0)
    keltner_upper = ind.get('keltner_upper', float('inf'))
    bb_lower = ind.get('bb_lower', 0)
    bb_upper = ind.get('bb_upper', float('inf'))
    
    rsi14 = ind.get('rsi14', 50)
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # LONG: Spike below then fade back up
    spike_below = low <= keltner_lower or low <= bb_lower
    rsi_oversold = 25 <= rsi14 <= 35
    trigger_up = close > prev_high
    
    if spike_below and rsi_oversold and trigger_up:
        return {
            "side": "LONG",
            "reason": f"NY session fade up (spike to {low:.2f}, RSI={rsi14:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.7,
                "tp_rr_multiple": 1.8,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": 0.8
            }
        }
    
    # SHORT: Spike above then fade back down
    spike_above = high >= keltner_upper or high >= bb_upper
    rsi_overbought = 65 <= rsi14 <= 75
    trigger_down = close < prev_low
    
    if spike_above and rsi_overbought and trigger_down:
        return {
            "side": "SHORT",
            "reason": f"NY session fade down (spike to {high:.2f}, RSI={rsi14:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.7,
                "tp_rr_multiple": 1.8,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": 0.8
            }
        }
    
    return None


def regime_adaptive_core_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Regime Adaptive Core
    Category: Advanced / Auto-Selection
    
    Auto-selects strategy based on market regime:
    - ADX >= 22: Trend pullback logic
    - Squeeze (bb_bw_pct <= 35): Breakout logic (Keltner/Donchian)
    - ADX < 18 no squeeze: Mean reversion (BB/VWAP)
    
    Exits: Dynamic based on regime
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    adx14 = ind.get('adx14', 0)
    bb_bw_pct = ind.get('bb_bw_pct', 100)
    
    # Regime detection
    is_trend = adx14 >= 22
    is_squeeze = bb_bw_pct <= 35
    is_range = adx14 < 18 and not is_squeeze
    
    # =========================================================================
    # MODE 1: TREND (ADX >= 22) - Pullback strategy
    # =========================================================================
    if is_trend:
        ema20 = ind.get('ema20', 0)
        ema50 = ind.get('ema50', 0)
        ema200 = ind.get('ema200', 0)
        rsi14 = ind.get('rsi14', 50)
        low = bar['low']
        high = bar['high']
        prev_high = ind.get('prev_high', float('inf'))
        prev_low = ind.get('prev_low', 0)
        
        # LONG: Pullback in uptrend
        if close > ema200:
            pullback = low <= ema20 or low <= ema50
            rsi_ok = 40 <= rsi14 <= 55
            trigger = close > prev_high
            
            if pullback and rsi_ok and trigger:
                return {
                    "side": "LONG",
                    "reason": f"Adaptive TREND pullback (ADX={adx14:.1f}, RSI={rsi14:.1f})",
                    "regime_hint": "trend",
                    "meta": {
                        "sl_tp_style": "chandelier",
                        "sl_atr_mult": 2.0,
                        "tp_rr_multiple": 2.5,
                        "trail_atr_mult": 2.5,
                        "breakeven_at_R": None
                    }
                }
        
        # SHORT: Pullback in downtrend
        if close < ema200:
            pullback_short = high >= ema20 or high >= ema50
            rsi_ok_short = 45 <= rsi14 <= 60
            trigger_short = close < prev_low
            
            if pullback_short and rsi_ok_short and trigger_short:
                return {
                    "side": "SHORT",
                    "reason": f"Adaptive TREND pullback down (ADX={adx14:.1f}, RSI={rsi14:.1f})",
                    "regime_hint": "trend",
                    "meta": {
                        "sl_tp_style": "chandelier",
                        "sl_atr_mult": 2.0,
                        "tp_rr_multiple": 2.5,
                        "trail_atr_mult": 2.5,
                        "breakeven_at_R": None
                    }
                }
    
    # =========================================================================
    # MODE 2: SQUEEZE - Breakout strategy
    # =========================================================================
    elif is_squeeze:
        keltner_upper = ind.get('keltner_upper', float('inf'))
        keltner_lower = ind.get('keltner_lower', 0)
        donchian_high = ind.get('donchian_high20', float('inf'))
        donchian_low = ind.get('donchian_low20', 0)
        
        # LONG: Breakout
        if close > keltner_upper or close > donchian_high:
            return {
                "side": "LONG",
                "reason": f"Adaptive SQUEEZE breakout (BW={bb_bw_pct:.1f}%)",
                "regime_hint": "low_vol",
                "meta": {
                    "sl_tp_style": "atr_trailing",
                    "sl_atr_mult": 2.0,
                    "tp_rr_multiple": 2.2,
                    "trail_atr_mult": 2.2,
                    "breakeven_at_R": None
                }
            }
        
        # SHORT: Breakdown
        if close < keltner_lower or close < donchian_low:
            return {
                "side": "SHORT",
                "reason": f"Adaptive SQUEEZE breakdown (BW={bb_bw_pct:.1f}%)",
                "regime_hint": "low_vol",
                "meta": {
                    "sl_tp_style": "atr_trailing",
                    "sl_atr_mult": 2.0,
                    "tp_rr_multiple": 2.2,
                    "trail_atr_mult": 2.2,
                    "breakeven_at_R": None
                }
            }
    
    # =========================================================================
    # MODE 3: RANGE (ADX < 18, no squeeze) - Mean reversion
    # =========================================================================
    elif is_range:
        bb_lower = ind.get('bb_lower', 0)
        bb_upper = ind.get('bb_upper', float('inf'))
        vwap = ind.get('vwap', close)
        rsi14 = ind.get('rsi14', 50)
        prev_high = ind.get('prev_high', float('inf'))
        prev_low = ind.get('prev_low', 0)
        
        # LONG: Mean reversion from BB lower or below VWAP
        touch_lower = close <= bb_lower * 1.01
        below_vwap = close < vwap * 0.99
        rsi_oversold = 30 <= rsi14 <= 40
        trigger = close > prev_high
        
        if (touch_lower or below_vwap) and rsi_oversold and trigger:
            return {
                "side": "LONG",
                "reason": f"Adaptive RANGE reversion (ADX={adx14:.1f}, RSI={rsi14:.1f})",
                "regime_hint": "range",
                "meta": {
                    "sl_tp_style": "keltner",
                    "sl_atr_mult": 1.6,
                    "tp_rr_multiple": 1.8,
                    "trail_atr_mult": None,
                    "breakeven_at_R": None
                }
            }
        
        # SHORT: Mean reversion from BB upper or above VWAP
        touch_upper = close >= bb_upper * 0.99
        above_vwap = close > vwap * 1.01
        rsi_overbought = 60 <= rsi14 <= 70
        trigger_short = close < prev_low
        
        if (touch_upper or above_vwap) and rsi_overbought and trigger_short:
            return {
                "side": "SHORT",
                "reason": f"Adaptive RANGE reversion down (ADX={adx14:.1f}, RSI={rsi14:.1f})",
                "regime_hint": "range",
                "meta": {
                    "sl_tp_style": "keltner",
                    "sl_atr_mult": 1.6,
                    "tp_rr_multiple": 1.8,
                    "trail_atr_mult": None,
                    "breakeven_at_R": None
                }
            }
    
    return None


def pure_price_action_donchian_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Pure Price Action Donchian
    Category: Price Action / Trend
    
    LONG: close>ema200 + pullback doesn't lose donchian_low20 + break donchian_high20
    SHORT: inverse
    Exits: atr_fixed, sl=1.9, tp=2.3
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    low = bar['low']
    high = bar['high']
    
    ema200 = ind.get('ema200', 0)
    donchian_high = ind.get('donchian_high20', float('inf'))
    donchian_low = ind.get('donchian_low20', 0)
    
    # LONG: Uptrend structure
    if close > ema200:
        # Pullback that doesn't break below donchian_low (structure intact)
        pullback_held = low > donchian_low
        # Now breaking above donchian_high
        breakout = close > donchian_high
        
        if pullback_held and breakout:
            return {
                "side": "LONG",
                "reason": f"Price action Donchian breakout (structure held at {donchian_low:.2f})",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "atr_fixed",
                    "sl_atr_mult": 1.9,
                    "tp_rr_multiple": 2.3,
                    "trail_atr_mult": None,
                    "breakeven_at_R": None
                }
            }
    
    # SHORT: Downtrend structure
    if close < ema200:
        # Pullback that doesn't break above donchian_high
        pullback_held_short = high < donchian_high
        # Now breaking below donchian_low
        breakdown = close < donchian_low
        
        if pullback_held_short and breakdown:
            return {
                "side": "SHORT",
                "reason": f"Price action Donchian breakdown (structure held at {donchian_high:.2f})",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "atr_fixed",
                    "sl_atr_mult": 1.9,
                    "tp_rr_multiple": 2.3,
                    "trail_atr_mult": None,
                    "breakeven_at_R": None
                }
            }
    
    return None


def order_flow_momentum_vwap_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Order Flow Momentum VWAP
    Category: Volume / Momentum
    
    LONG: close>vwap + MFI rising (Δ MFI > threshold) + ADX rising + break prev_high
    SHORT: symmetric
    Exits: supertrend, sl=2.0, tp=2.2
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    vwap = ind.get('vwap', close)
    
    mfi = ind.get('mfi', 50)
    mfi_prev = ind.get('mfi_prev', 50)
    mfi_5ago = ind.get('mfi_5bars_ago', 50)
    
    adx14 = ind.get('adx14', 0)
    adx14_prev = ind.get('adx14_prev', 0)
    
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # MFI momentum threshold
    mfi_delta = mfi - mfi_5ago
    mfi_rising = mfi_delta > 5  # MFI increased by 5+ points
    adx_rising = adx14 > adx14_prev
    
    # LONG: Order flow bullish
    if close > vwap and mfi_rising and adx_rising and close > prev_high:
        return {
            "side": "LONG",
            "reason": f"Order flow momentum (MFI Δ={mfi_delta:.1f}, ADX rising to {adx14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "supertrend",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Order flow bearish
    mfi_falling = mfi_delta < -5  # MFI decreased by 5+ points
    
    if close < vwap and mfi_falling and adx_rising and close < prev_low:
        return {
            "side": "SHORT",
            "reason": f"Order flow momentum down (MFI Δ={mfi_delta:.1f}, ADX rising to {adx14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "supertrend",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


ADVANCED_STRATEGIES = {
    "london_breakout_atr": london_breakout_atr_entry_signal,
    "ny_session_fade": ny_session_fade_entry_signal,
    "regime_adaptive_core": regime_adaptive_core_entry_signal,
    "pure_price_action_donchian": pure_price_action_donchian_entry_signal,
    "order_flow_momentum_vwap": order_flow_momentum_vwap_entry_signal,
}


def get_strategy(name: str):
    """Get strategy function by name"""
    return ADVANCED_STRATEGIES.get(name)


def list_strategies():
    """List all available advanced strategies"""
    return list(ADVANCED_STRATEGIES.keys())