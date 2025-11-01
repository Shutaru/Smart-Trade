"""
Refinement Strategies (31-35)

Implementation of refined professional strategies with:
- RSI + SuperTrend flip detection
- Keltner pullback continuation
- EMA200 tap reversion
- Double Donchian pullback (multi-timeframe concept)
- Volatility-weighted breakout (ATR filtering)

Regime: trend, range/trend pullback, managed_breakout
"""

from typing import Optional, Dict, Any


def rsi_supertrend_flip_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: RSI SuperTrend Flip
    Category: Trend / Reversal Detection
    
    LONG: supertrend flips bear->bull + RSI14 crosses above 50 + close>ema50
    SHORT: flip bull->bear + RSI crosses below 50
    Exits: chandelier, sl=2.0, trail=2.2, tp=2.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    ema50 = ind.get('ema50', 0)
    
    # SuperTrend flip detection
    supertrend_bull = ind.get('supertrend_bull', False)
    supertrend_bear = ind.get('supertrend_bear', False)
    supertrend_bull_prev = ind.get('supertrend_bull_prev', False)
    supertrend_bear_prev = ind.get('supertrend_bear_prev', False)
    
    # RSI crossover
    rsi14 = ind.get('rsi14', 50)
    rsi14_prev = ind.get('rsi14_prev', 50)
    
    # LONG: Bear->Bull flip + RSI crosses 50 up
    st_flip_bullish = supertrend_bear_prev and supertrend_bull
    rsi_cross_up = rsi14_prev <= 50 and rsi14 > 50
    
    if st_flip_bullish and rsi_cross_up and close > ema50:
        return {
            "side": "LONG",
            "reason": f"SuperTrend flip to bull + RSI cross 50 (RSI {rsi14_prev:.1f}->{rsi14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "chandelier",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Bull->Bear flip + RSI crosses 50 down
    st_flip_bearish = supertrend_bull_prev and supertrend_bear
    rsi_cross_down = rsi14_prev >= 50 and rsi14 < 50
    
    if st_flip_bearish and rsi_cross_down and close < ema50:
        return {
            "side": "SHORT",
            "reason": f"SuperTrend flip to bear + RSI cross 50 (RSI {rsi14_prev:.1f}->{rsi14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "chandelier",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": None
            }
        }
    
    return None


def keltner_pullback_continuation_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Keltner Pullback Continuation
    Category: Trend Following
    
    LONG: uptrend + pullback to Keltner midline + resume with close>ema20
    SHORT: symmetric
    Exits: atr_trailing, sl=1.8, trail=2.1, tp=2.1
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    low = bar['low']
    high = bar['high']
    
    keltner_mid = ind.get('keltner_mid', close)
    keltner_upper = ind.get('keltner_upper', float('inf'))
    keltner_lower = ind.get('keltner_lower', 0)
    
    ema20 = ind.get('ema20', 0)
    ema50 = ind.get('ema50', 0)
    ema200 = ind.get('ema200', 0)
    
    # LONG: Uptrend pullback to midline
    uptrend = close > ema200 and ema50 > ema200
    pullback_to_mid = low <= keltner_mid * 1.01  # Touch or near midline
    resume = close > ema20
    
    if uptrend and pullback_to_mid and resume:
        return {
            "side": "LONG",
            "reason": f"Keltner midline pullback resume (touched {keltner_mid:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.1,
                "trail_atr_mult": 2.1,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Downtrend pullback to midline
    downtrend = close < ema200 and ema50 < ema200
    pullback_to_mid_short = high >= keltner_mid * 0.99
    resume_short = close < ema20
    
    if downtrend and pullback_to_mid_short and resume_short:
        return {
            "side": "SHORT",
            "reason": f"Keltner midline pullback resume down (touched {keltner_mid:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.1,
                "trail_atr_mult": 2.1,
                "breakeven_at_R": None
            }
        }
    
    return None


def ema200_tap_reversion_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: EMA200 Tap Reversion
    Category: Mean Reversion / Trend Pullback
    
    LONG: close>ema200 + light touch/sweep of ema200 + RSI 35-50 + trigger up
    SHORT: close<ema200 touch from below
    Exits: breakeven_then_trail, sl=1.7, tp=1.9, be=0.9
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    low = bar['low']
    high = bar['high']
    
    ema200 = ind.get('ema200', 0)
    rsi14 = ind.get('rsi14', 50)
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # LONG: Price above EMA200, touches it from above
    above_ema200 = close > ema200
    touched_ema200 = low <= ema200 * 1.005  # Within 0.5% touch
    rsi_ok = 35 <= rsi14 <= 50
    trigger = close > prev_high
    
    if above_ema200 and touched_ema200 and rsi_ok and trigger:
        return {
            "side": "LONG",
            "reason": f"EMA200 tap reversion (touched {ema200:.2f}, RSI={rsi14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.7,
                "tp_rr_multiple": 1.9,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": 0.9
            }
        }
    
    # SHORT: Price below EMA200, touches it from below
    below_ema200 = close < ema200
    touched_ema200_short = high >= ema200 * 0.995
    rsi_ok_short = 50 <= rsi14 <= 65
    trigger_short = close < prev_low
    
    if below_ema200 and touched_ema200_short and rsi_ok_short and trigger_short:
        return {
            "side": "SHORT",
            "reason": f"EMA200 tap reversion down (touched {ema200:.2f}, RSI={rsi14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.7,
                "tp_rr_multiple": 1.9,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": 0.9
            }
        }
    
    return None


def double_donchian_pullback_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Double Donchian Pullback
    Category: Trend / Multi-Timeframe Concept
    
    LONG: close>donchian_high20 (break) + pullback stays above donchian_high10 + resume close>prev_high
    SHORT: symmetric
    Exits: atr_fixed, sl=2.0, tp=2.4
    
    Note: Requires both Donchian(20) and Donchian(10) channels
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    low = bar['low']
    high = bar['high']
    
    # Donchian channels (20-period and 10-period)
    donchian_high20 = ind.get('donchian_high20', float('inf'))
    donchian_low20 = ind.get('donchian_low20', 0)
    donchian_high10 = ind.get('donchian_high10', float('inf'))
    donchian_low10 = ind.get('donchian_low10', 0)
    
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # LONG: Break 20-period high, pullback holds above 10-period high
    broke_20_high = close > donchian_high20
    pullback_held = low > donchian_high10  # Structure preserved
    resume = close > prev_high
    
    # Allow entry if either broke recently OR holding structure
    if (broke_20_high or pullback_held) and resume and close > donchian_high10:
        return {
            "side": "LONG",
            "reason": f"Double Donchian pullback (D20={donchian_high20:.2f}, held D10={donchian_high10:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.4,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Break 20-period low, pullback holds below 10-period low
    broke_20_low = close < donchian_low20
    pullback_held_short = high < donchian_low10
    resume_short = close < prev_low
    
    if (broke_20_low or pullback_held_short) and resume_short and close < donchian_low10:
        return {
            "side": "SHORT",
            "reason": f"Double Donchian pullback down (D20={donchian_low20:.2f}, held D10={donchian_low10:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.4,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


def volatility_weighted_breakout_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Volatility Weighted Breakout
    Category: Breakout / Volatility Filter
    
    LONG: Donchian/Keltner breakout only if ATR percentile in [40-80] (avoid extremes) + ADX rising
    SHORT: symmetric
    Exits: supertrend, sl=2.1, tp=2.3
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # ATR volatility filter
    atr_norm_pct = ind.get('atr_norm_pct', 50)
    atr_in_range = 40 <= atr_norm_pct <= 80
    
    # ADX momentum
    adx14 = ind.get('adx14', 0)
    adx14_prev = ind.get('adx14_prev', 0)
    adx_rising = adx14 > adx14_prev
    
    # Breakout levels
    donchian_high = ind.get('donchian_high20', float('inf'))
    donchian_low = ind.get('donchian_low20', 0)
    keltner_upper = ind.get('keltner_upper', float('inf'))
    keltner_lower = ind.get('keltner_lower', 0)
    
    # LONG: Breakout with volatility filter
    breakout = close > donchian_high or close > keltner_upper
    
    if breakout and atr_in_range and adx_rising:
        return {
            "side": "LONG",
            "reason": f"Vol-weighted breakout (ATR pct={atr_norm_pct:.1f}, ADX {adx14_prev:.1f}->{adx14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "supertrend",
                "sl_atr_mult": 2.1,
                "tp_rr_multiple": 2.3,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Breakdown with volatility filter
    breakdown = close < donchian_low or close < keltner_lower
    
    if breakdown and atr_in_range and adx_rising:
        return {
            "side": "SHORT",
            "reason": f"Vol-weighted breakdown (ATR pct={atr_norm_pct:.1f}, ADX {adx14_prev:.1f}->{adx14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "supertrend",
                "sl_atr_mult": 2.1,
                "tp_rr_multiple": 2.3,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


REFINEMENT_STRATEGIES = {
    "rsi_supertrend_flip": rsi_supertrend_flip_entry_signal,
    "keltner_pullback_continuation": keltner_pullback_continuation_entry_signal,
    "ema200_tap_reversion": ema200_tap_reversion_entry_signal,
    "double_donchian_pullback": double_donchian_pullback_entry_signal,
    "volatility_weighted_breakout": volatility_weighted_breakout_entry_signal,
}


def get_strategy(name: str):
    """Get strategy function by name"""
    return REFINEMENT_STRATEGIES.get(name)


def list_strategies():
    """List all available refinement strategies"""
    return list(REFINEMENT_STRATEGIES.keys())