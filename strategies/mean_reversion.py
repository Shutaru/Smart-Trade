"""
Mean Reversion Strategies (6-10)

Implementation of professional mean-reversion strategies with:
- RSI + Bollinger Bands extremes
- Stochastic oversold/overbought reversals
- Bollinger Band mean reversion
- CCI extreme snapback
- MFI divergence detection

Regime: range markets (low ADX, ranging price action)
"""

from typing import Optional, Dict, Any


def rsi_band_reversion_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: RSI Band Reversion
    Category: Mean Reversion
    
    LONG: close near ema50 or touch BB lower, RSI 25-35, trigger close>prev_high
    SHORT: BB upper + RSI 65-75, trigger close<prev_low
    Exits: breakeven_then_trail, sl=1.5, tp=1.8, be=0.8, trail=2.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # LONG
    ema50 = ind.get('ema50', 0)
    bb_lower = ind.get('bb_lower', 0)
    rsi14 = ind.get('rsi14', 50)
    prev_high = ind.get('prev_high', float('inf'))
    
    near_ema50 = abs(close - ema50) < (ema50 * 0.01)  # Within 1%
    touch_bb_lower = close <= bb_lower * 1.01  # Touch or below BB lower
    
    if (near_ema50 or touch_bb_lower) and 25 <= rsi14 <= 35 and close > prev_high:
        return {
            "side": "LONG",
            "reason": f"RSI oversold ({rsi14:.1f}) + BB lower touch, mean reversion",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.5,
                "tp_rr_multiple": 1.8,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": 0.8
            }
        }
    
    # SHORT
    bb_upper = ind.get('bb_upper', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    touch_bb_upper = close >= bb_upper * 0.99  # Touch or above BB upper
    
    if touch_bb_upper and 65 <= rsi14 <= 75 and close < prev_low:
        return {
            "side": "SHORT",
            "reason": f"RSI overbought ({rsi14:.1f}) + BB upper touch, mean reversion",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.5,
                "tp_rr_multiple": 1.8,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": 0.8
            }
        }
    
    return None


def stoch_signal_reversal_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Stochastic Signal Reversal
    Category: Mean Reversion
    
    LONG: %K crosses above %D, both <25, close>=ema50, RSI 35-55
    SHORT: %K crosses below %D, both >75, close<=ema50
    Exits: atr_fixed, sl=1.6, tp=1.6
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    ema50 = ind.get('ema50', 0)
    
    stoch_k = ind.get('stoch_k', 50)
    stoch_d = ind.get('stoch_d', 50)
    stoch_k_prev = ind.get('stoch_k_prev', 50)
    stoch_d_prev = ind.get('stoch_d_prev', 50)
    rsi14 = ind.get('rsi14', 50)
    
    # LONG: %K crosses above %D in oversold zone
    k_cross_above_d = stoch_k_prev <= stoch_d_prev and stoch_k > stoch_d
    both_oversold = stoch_k < 25 and stoch_d < 25
    
    if k_cross_above_d and both_oversold and close >= ema50 and 35 <= rsi14 <= 55:
        return {
            "side": "LONG",
            "reason": f"Stoch oversold crossover (K={stoch_k:.1f}, D={stoch_d:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 1.6,
                "tp_rr_multiple": 1.6,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: %K crosses below %D in overbought zone
    k_cross_below_d = stoch_k_prev >= stoch_d_prev and stoch_k < stoch_d
    both_overbought = stoch_k > 75 and stoch_d > 75
    
    if k_cross_below_d and both_overbought and close <= ema50 and 45 <= rsi14 <= 65:
        return {
            "side": "SHORT",
            "reason": f"Stoch overbought crossover (K={stoch_k:.1f}, D={stoch_d:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 1.6,
                "tp_rr_multiple": 1.6,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


def bollinger_mean_reversion_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Bollinger Mean Reversion
    Category: Mean Reversion
    
    LONG: close outside/at BB lower then closes back inside, RSI 30-45
    SHORT: symmetric with BB upper
    Exits: keltner, sl=1.7, tp=1.7
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    close_prev = ind.get('close_prev', close)
    
    bb_lower = ind.get('bb_lower', 0)
    bb_upper = ind.get('bb_upper', float('inf'))
    bb_middle = ind.get('bb_middle', close)
    rsi14 = ind.get('rsi14', 50)
    
    # LONG: Was outside/at lower band, now closing back inside
    was_outside_lower = close_prev <= bb_lower
    now_inside = close > bb_lower and close < bb_middle
    
    if was_outside_lower and now_inside and 30 <= rsi14 <= 45:
        return {
            "side": "LONG",
            "reason": f"BB lower reversion (close back inside from {close_prev:.2f} to {close:.2f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "keltner",
                "sl_atr_mult": 1.7,
                "tp_rr_multiple": 1.7,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Was outside/at upper band, now closing back inside
    was_outside_upper = close_prev >= bb_upper
    now_inside_short = close < bb_upper and close > bb_middle
    
    if was_outside_upper and now_inside_short and 55 <= rsi14 <= 70:
        return {
            "side": "SHORT",
            "reason": f"BB upper reversion (close back inside from {close_prev:.2f} to {close:.2f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "keltner",
                "sl_atr_mult": 1.7,
                "tp_rr_multiple": 1.7,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


def cci_extreme_snapback_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: CCI Extreme Snapback
    Category: Mean Reversion
    
    LONG: CCI was <-100, now crosses back above -100, low<=ema20 or ema50
    SHORT: CCI was >+100, now crosses back below +100
    Exits: atr_trailing, sl=1.6, trail=1.8, tp=1.8
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    low = bar['low']
    high = bar['high']
    
    cci = ind.get('cci', 0)
    cci_prev = ind.get('cci_prev', 0)
    ema20 = ind.get('ema20', 0)
    ema50 = ind.get('ema50', 0)
    
    # LONG: CCI crosses back above -100 from extreme oversold
    cci_was_extreme_low = cci_prev < -100
    cci_crosses_back = cci >= -100
    touched_ema = low <= ema20 or low <= ema50
    
    if cci_was_extreme_low and cci_crosses_back and touched_ema:
        return {
            "side": "LONG",
            "reason": f"CCI extreme snapback ({cci_prev:.1f} -> {cci:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.6,
                "tp_rr_multiple": 1.8,
                "trail_atr_mult": 1.8,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: CCI crosses back below +100 from extreme overbought
    cci_was_extreme_high = cci_prev > 100
    cci_crosses_back_down = cci <= 100
    touched_ema_short = high >= ema20 or high >= ema50
    
    if cci_was_extreme_high and cci_crosses_back_down and touched_ema_short:
        return {
            "side": "SHORT",
            "reason": f"CCI extreme snapback ({cci_prev:.1f} -> {cci:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.6,
                "tp_rr_multiple": 1.8,
                "trail_atr_mult": 1.8,
                "breakeven_at_R": None
            }
        }
    
    return None


def mfi_divergence_reversion_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: MFI Divergence Reversion
    Category: Mean Reversion
    
    LONG: Bullish divergence (price LL, MFI HL) + close>ema20
    SHORT: Bearish divergence (price HH, MFI LH)
    Exits: breakeven_then_trail, sl=1.8, tp=2.0, be=1.0
    
    Note: Simplified divergence detection (requires lookback state)
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    ema20 = ind.get('ema20', 0)
    
    mfi = ind.get('mfi', 50)
    mfi_prev = ind.get('mfi_prev', 50)
    
    close_prev = ind.get('close_prev', close)
    low = bar['low']
    high = bar['high']
    low_prev = ind.get('low_prev', low)
    high_prev = ind.get('high_prev', high)
    
    # LONG: Simplified bullish divergence
    # Price making lower low, but MFI making higher low
    price_lower_low = low < low_prev
    mfi_higher_low = mfi > mfi_prev and mfi < 40  # MFI oversold but rising
    
    if price_lower_low and mfi_higher_low and close > ema20:
        return {
            "side": "LONG",
            "reason": f"MFI bullish divergence (MFI={mfi:.1f}, rising from {mfi_prev:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": 1.0
            }
        }
    
    # SHORT: Simplified bearish divergence
    # Price making higher high, but MFI making lower high
    price_higher_high = high > high_prev
    mfi_lower_high = mfi < mfi_prev and mfi > 60  # MFI overbought but falling
    
    if price_higher_high and mfi_lower_high and close < ema20:
        return {
            "side": "SHORT",
            "reason": f"MFI bearish divergence (MFI={mfi:.1f}, falling from {mfi_prev:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": 1.0
            }
        }
    
    return None


MEAN_REVERSION_STRATEGIES = {
    "rsi_band_reversion": rsi_band_reversion_entry_signal,
    "stoch_signal_reversal": stoch_signal_reversal_entry_signal,
    "bollinger_mean_reversion": bollinger_mean_reversion_entry_signal,
    "cci_extreme_snapback": cci_extreme_snapback_entry_signal,
    "mfi_divergence_reversion": mfi_divergence_reversion_entry_signal,
}


def get_strategy(name: str):
    """Get strategy function by name"""
    return MEAN_REVERSION_STRATEGIES.get(name)


def list_strategies():
    """List all available mean reversion strategies"""
    return list(MEAN_REVERSION_STRATEGIES.keys())