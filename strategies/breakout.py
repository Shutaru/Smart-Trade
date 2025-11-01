"""
Breakout / Volatility Expansion Strategies (11-15)

Implementation of professional breakout strategies with:
- Bollinger Squeeze detection and expansion
- Keltner channel breakouts
- ATR expansion detection
- Donchian volatility breakouts
- Channel squeeze confirmation

Regime: low_vol -> expansion, range -> trend, high_vol
"""

from typing import Optional, Dict, Any


def bollinger_squeeze_breakout_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Bollinger Squeeze Breakout
    Category: Breakout / Volatility Expansion
    
    LONG: Squeeze (bb_bw_pct<=35 or boll_in_keltner) + close>BB_upper + ADX rising
    SHORT: symmetric with BB_lower
    Exits: chandelier, sl=2.0, trail=2.5, tp=2.2
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # Detect squeeze
    bb_bw_pct = ind.get('bb_bw_pct', 100)
    boll_in_keltner = ind.get('boll_in_keltner', False)
    squeeze = bb_bw_pct <= 35 or boll_in_keltner
    
    # ADX momentum
    adx14 = ind.get('adx14', 0)
    adx14_prev = ind.get('adx14_prev', 0)
    adx_rising = adx14 > adx14_prev
    
    # LONG: Breakout above BB upper
    bb_upper = ind.get('bb_upper', float('inf'))
    
    if squeeze and close > bb_upper and adx_rising:
        return {
            "side": "LONG",
            "reason": f"BB Squeeze breakout (BW={bb_bw_pct:.1f}%, ADX rising to {adx14:.1f})",
            "regime_hint": "low_vol",
            "meta": {
                "sl_tp_style": "chandelier",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.5,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Breakdown below BB lower
    bb_lower = ind.get('bb_lower', 0)
    
    if squeeze and close < bb_lower and adx_rising:
        return {
            "side": "SHORT",
            "reason": f"BB Squeeze breakdown (BW={bb_bw_pct:.1f}%, ADX rising to {adx14:.1f})",
            "regime_hint": "low_vol",
            "meta": {
                "sl_tp_style": "chandelier",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.5,
                "breakeven_at_R": None
            }
        }
    
    return None


def keltner_expansion_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Keltner Expansion
    Category: Breakout
    
    LONG: close>keltner_upper + ADX rising + RSI<=70
    SHORT: close<keltner_lower + RSI>=30
    Exits: atr_trailing, sl=2.0, trail=2.2, tp=2.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    keltner_upper = ind.get('keltner_upper', float('inf'))
    keltner_lower = ind.get('keltner_lower', 0)
    
    adx14 = ind.get('adx14', 0)
    adx14_5ago = ind.get('adx14_5bars_ago', 0)
    adx_rising = adx14 > adx14_5ago
    
    rsi14 = ind.get('rsi14', 50)
    
    # LONG
    if close > keltner_upper and adx_rising and rsi14 <= 70:
        return {
            "side": "LONG",
            "reason": f"Keltner upper breakout (ADX {adx14_5ago:.1f}->{adx14:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": None
            }
        }
    
    # SHORT
    if close < keltner_lower and adx_rising and rsi14 >= 30:
        return {
            "side": "SHORT",
            "reason": f"Keltner lower breakdown (ADX {adx14_5ago:.1f}->{adx14:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": None
            }
        }
    
    return None


def atr_expansion_breakout_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: ATR Expansion Breakout
    Category: Breakout / High Volatility
    
    LONG: atr_norm_pct rises above 70th percentile + break prev_high + long_filters
    SHORT: symmetric
    Exits: supertrend, sl=2.2, tp=2.4
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # ATR expansion detection
    atr_norm_pct = ind.get('atr_norm_pct', 50)  # ATR percentile (0-100)
    atr_expanding = atr_norm_pct >= 70
    
    # LONG filters
    long_filters = (
        close > ind.get('ema200', 0) and
        ind.get('supertrend_bull', False) and
        ind.get('adx14', 0) >= 18
    )
    
    prev_high = ind.get('prev_high', float('inf'))
    
    if atr_expanding and close > prev_high and long_filters:
        return {
            "side": "LONG",
            "reason": f"ATR expansion breakout (ATR pct={atr_norm_pct:.1f})",
            "regime_hint": "high_vol",
            "meta": {
                "sl_tp_style": "supertrend",
                "sl_atr_mult": 2.2,
                "tp_rr_multiple": 2.4,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT filters
    short_filters = (
        close < ind.get('ema200', float('inf')) and
        ind.get('supertrend_bear', False) and
        ind.get('adx14', 0) >= 18
    )
    
    prev_low = ind.get('prev_low', 0)
    
    if atr_expanding and close < prev_low and short_filters:
        return {
            "side": "SHORT",
            "reason": f"ATR expansion breakdown (ATR pct={atr_norm_pct:.1f})",
            "regime_hint": "high_vol",
            "meta": {
                "sl_tp_style": "supertrend",
                "sl_atr_mult": 2.2,
                "tp_rr_multiple": 2.4,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


def donchian_volatility_breakout_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Donchian Volatility Breakout
    Category: Breakout
    
    LONG: close>donchian_high20 + (previous squeeze OR ADX rising)
    SHORT: close<donchian_low20
    Exits: atr_fixed, sl=2.0, tp=2.5
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    donchian_high = ind.get('donchian_high20', float('inf'))
    donchian_low = ind.get('donchian_low20', 0)
    
    # Squeeze or ADX momentum
    bb_bw_pct = ind.get('bb_bw_pct', 100)
    bb_bw_pct_prev = ind.get('bb_bw_pct_prev', 100)
    had_squeeze = bb_bw_pct_prev <= 35
    
    adx14 = ind.get('adx14', 0)
    adx14_5ago = ind.get('adx14_5bars_ago', 0)
    adx_rising = adx14 > adx14_5ago
    
    confirmation = had_squeeze or adx_rising
    
    # LONG
    if close > donchian_high and confirmation:
        reason = "post-squeeze" if had_squeeze else f"ADX rising ({adx14_5ago:.1f}->{adx14:.1f})"
        return {
            "side": "LONG",
            "reason": f"Donchian breakout {reason}",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.5,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT
    if close < donchian_low and confirmation:
        reason = "post-squeeze" if had_squeeze else f"ADX rising ({adx14_5ago:.1f}->{adx14:.1f})"
        return {
            "side": "SHORT",
            "reason": f"Donchian breakdown {reason}",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.5,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


def channel_squeeze_plus_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Channel Squeeze Plus
    Category: Breakout
    
    LONG: BB inside Keltner + ADX rising + close>keltner_upper
    SHORT: symmetric with keltner_lower
    Exits: chandelier, sl=2.0, trail=2.5, tp=2.2
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # Squeeze: BB inside Keltner
    boll_in_keltner = ind.get('boll_in_keltner', False)
    
    # ADX momentum
    adx14 = ind.get('adx14', 0)
    adx14_prev = ind.get('adx14_prev', 0)
    adx_rising = adx14 > adx14_prev
    
    keltner_upper = ind.get('keltner_upper', float('inf'))
    keltner_lower = ind.get('keltner_lower', 0)
    
    # LONG
    if boll_in_keltner and adx_rising and close > keltner_upper:
        return {
            "side": "LONG",
            "reason": f"Channel squeeze breakout (ADX {adx14_prev:.1f}->{adx14:.1f})",
            "regime_hint": "low_vol",
            "meta": {
                "sl_tp_style": "chandelier",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.5,
                "breakeven_at_R": None
            }
        }
    
    # SHORT
    if boll_in_keltner and adx_rising and close < keltner_lower:
        return {
            "side": "SHORT",
            "reason": f"Channel squeeze breakdown (ADX {adx14_prev:.1f}->{adx14:.1f})",
            "regime_hint": "low_vol",
            "meta": {
                "sl_tp_style": "chandelier",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.5,
                "breakeven_at_R": None
            }
        }
    
    return None


BREAKOUT_STRATEGIES = {
    "bollinger_squeeze_breakout": bollinger_squeeze_breakout_entry_signal,
    "keltner_expansion": keltner_expansion_entry_signal,
    "atr_expansion_breakout": atr_expansion_breakout_entry_signal,
    "donchian_volatility_breakout": donchian_volatility_breakout_entry_signal,
    "channel_squeeze_plus": channel_squeeze_plus_entry_signal,
}


def get_strategy(name: str):
    """Get strategy function by name"""
    return BREAKOUT_STRATEGIES.get(name)


def list_strategies():
    """List all available breakout strategies"""
    return list(BREAKOUT_STRATEGIES.keys())