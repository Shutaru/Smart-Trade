"""
Trend Following Strategies (1-5)

Implementation of professional trend-following strategies with:
- SuperTrend + ADX momentum
- EMA cloud pullbacks
- Donchian continuation
- MACD trend alignment
- ADX regime filtering
"""

from typing import Optional, Dict, Any


def trendflow_supertrend_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: TrendFlow SuperTrend
    Category: Trend Following
    
    LONG: supertrend_bull + adx>=22 + (breakout OR pullback)
    SHORT: symmetric
    Exits: chandelier, sl=2.0, trail=2.5, tp=2.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # LONG
    long_filters = (
        close > ind.get('ema200', 0) and
        ind.get('supertrend_bull', False) and
        ind.get('adx14', 0) >= 22
    )
    
    if long_filters:
        breakout = close > ind.get('prev_high', float('inf'))
        rsi14 = ind.get('rsi14', 50)
        ema20 = ind.get('ema20', 0)
        ema20_prev = ind.get('ema20_prev', 0)
        pullback = (40 <= rsi14 <= 55 and close > ema20 and close > ema20_prev)
        
        if breakout or pullback:
            reason = "Breakout prev_high" if breakout else "Pullback resume"
            return {
                "side": "LONG",
                "reason": f"TrendFlow SuperTrend: {reason}, ADX={ind.get('adx14', 0):.1f}",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "chandelier",
                    "sl_atr_mult": 2.0,
                    "tp_rr_multiple": 2.0,
                    "trail_atr_mult": 2.5,
                    "breakeven_at_R": None
                }
            }
    
    # SHORT
    short_filters = (
        close < ind.get('ema200', float('inf')) and
        ind.get('supertrend_bear', False) and
        ind.get('adx14', 0) >= 22
    )
    
    if short_filters:
        breakdown = close < ind.get('prev_low', 0)
        rsi14 = ind.get('rsi14', 50)
        ema20 = ind.get('ema20', float('inf'))
        ema20_prev = ind.get('ema20_prev', float('inf'))
        pullback = (45 <= rsi14 <= 60 and close < ema20 and close < ema20_prev)
        
        if breakdown or pullback:
            reason = "Breakdown prev_low" if breakdown else "Pullback resume"
            return {
                "side": "SHORT",
                "reason": f"TrendFlow SuperTrend: {reason}, ADX={ind.get('adx14', 0):.1f}",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "chandelier",
                    "sl_atr_mult": 2.0,
                    "tp_rr_multiple": 2.0,
                    "trail_atr_mult": 2.5,
                    "breakeven_at_R": None
                }
            }
    
    return None


def ema_cloud_trend_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: EMA Cloud Trend
    Category: Trend Following
    
    LONG: close>ema200, pullback to ema20/50, rsi 40-55, resume
    SHORT: symmetric
    Exits: breakeven_then_trail, sl=1.8, trail=2.2, tp=2.5
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    low = bar['low']
    high = bar['high']
    
    # LONG
    if close > ind.get('ema200', 0):
        ema20 = ind.get('ema20', 0)
        ema50 = ind.get('ema50', 0)
        ema20_prev = ind.get('ema20_prev', 0)
        rsi14 = ind.get('rsi14', 50)
        
        pullback = low <= ema50 or low <= ema20
        rsi_ok = 40 <= rsi14 <= 55
        trigger = close > ema20_prev or close > ind.get('prev_high', float('inf'))
        
        if pullback and rsi_ok and trigger:
            return {
                "side": "LONG",
                "reason": f"EMA Cloud pullback resume, RSI={rsi14:.1f}",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "breakeven_then_trail",
                    "sl_atr_mult": 1.8,
                    "tp_rr_multiple": 2.5,
                    "trail_atr_mult": 2.2,
                    "breakeven_at_R": 1.0
                }
            }
    
    # SHORT
    if close < ind.get('ema200', float('inf')):
        ema20 = ind.get('ema20', float('inf'))
        ema50 = ind.get('ema50', float('inf'))
        ema20_prev = ind.get('ema20_prev', float('inf'))
        rsi14 = ind.get('rsi14', 50)
        
        pullback = high >= ema50 or high >= ema20
        rsi_ok = 45 <= rsi14 <= 60
        trigger = close < ema20_prev or close < ind.get('prev_low', 0)
        
        if pullback and rsi_ok and trigger:
            return {
                "side": "SHORT",
                "reason": f"EMA Cloud pullback resume down, RSI={rsi14:.1f}",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "breakeven_then_trail",
                    "sl_atr_mult": 1.8,
                    "tp_rr_multiple": 2.5,
                    "trail_atr_mult": 2.2,
                    "breakeven_at_R": 1.0
                }
            }
    
    return None


def donchian_continuation_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Donchian Continuation
    Category: Trend Following / Breakout
    
    LONG: filters + close>donchian_high20 + adx rising
    SHORT: symmetric
    Exits: atr_trailing, sl=2.0, trail=2.0, tp=2.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # LONG
    long_filters = (
        close > ind.get('ema200', 0) and
        ind.get('supertrend_bull', False) and
        ind.get('adx14', 0) >= 18
    )
    
    if long_filters:
        donchian_high = ind.get('donchian_high20', float('inf'))
        adx14 = ind.get('adx14', 0)
        adx14_5ago = ind.get('adx14_5bars_ago', 0)
        
        if close > donchian_high and adx14 > adx14_5ago:
            return {
                "side": "LONG",
                "reason": f"Donchian breakout + ADX rising ({adx14:.1f} > {adx14_5ago:.1f})",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "atr_trailing",
                    "sl_atr_mult": 2.0,
                    "tp_rr_multiple": 2.0,
                    "trail_atr_mult": 2.0,
                    "breakeven_at_R": None
                }
            }
    
    # SHORT
    short_filters = (
        close < ind.get('ema200', float('inf')) and
        ind.get('supertrend_bear', False) and
        ind.get('adx14', 0) >= 18
    )
    
    if short_filters:
        donchian_low = ind.get('donchian_low20', 0)
        adx14 = ind.get('adx14', 0)
        adx14_5ago = ind.get('adx14_5bars_ago', 0)
        
        if close < donchian_low and adx14 > adx14_5ago:
            return {
                "side": "SHORT",
                "reason": f"Donchian breakdown + ADX rising ({adx14:.1f} > {adx14_5ago:.1f})",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "atr_trailing",
                    "sl_atr_mult": 2.0,
                    "tp_rr_multiple": 2.0,
                    "trail_atr_mult": 2.0,
                    "breakeven_at_R": None
                }
            }
    
    return None


def macd_zero_trend_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: MACD Zero Line Trend
    Category: Trend Following
    
    LONG: filters + macd_hist>0 + rsi<=70 + breakout
    SHORT: symmetric with macd_hist<0
    Exits: supertrend, sl=2.2, tp=2.2
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # LONG
    long_filters = (
        close > ind.get('ema200', 0) and
        ind.get('supertrend_bull', False) and
        ind.get('adx14', 0) >= 18
    )
    
    if long_filters:
        macd_hist = ind.get('macd_hist', 0)
        rsi14 = ind.get('rsi14', 100)
        prev_high = ind.get('prev_high', float('inf'))
        
        if macd_hist > 0 and rsi14 <= 70 and close > prev_high:
            return {
                "side": "LONG",
                "reason": f"MACD above zero + breakout, MACD_hist={macd_hist:.2f}",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "supertrend",
                    "sl_atr_mult": 2.2,
                    "tp_rr_multiple": 2.2,
                    "trail_atr_mult": None,
                    "breakeven_at_R": None
                }
            }
    
    # SHORT
    short_filters = (
        close < ind.get('ema200', float('inf')) and
        ind.get('supertrend_bear', False) and
        ind.get('adx14', 0) >= 18
    )
    
    if short_filters:
        macd_hist = ind.get('macd_hist', 0)
        rsi14 = ind.get('rsi14', 0)
        prev_low = ind.get('prev_low', 0)
        
        if macd_hist < 0 and rsi14 >= 30 and close < prev_low:
            return {
                "side": "SHORT",
                "reason": f"MACD below zero + breakdown, MACD_hist={macd_hist:.2f}",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "supertrend",
                    "sl_atr_mult": 2.2,
                    "tp_rr_multiple": 2.2,
                    "trail_atr_mult": None,
                    "breakeven_at_R": None
                }
            }
    
    return None


def adx_trend_filter_plus_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: ADX Trend Filter Plus
    Category: Trend Following
    
    LONG: close>ema200 + adx>=25 + rsi 42-55 + close>ema20_prev
    SHORT: symmetric with rsi 45-58
    Exits: atr_fixed, sl=1.8, tp=2.4
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # LONG
    if close > ind.get('ema200', 0):
        adx14 = ind.get('adx14', 0)
        rsi14 = ind.get('rsi14', 50)
        ema20_prev = ind.get('ema20_prev', 0)
        
        if adx14 >= 25 and 42 <= rsi14 <= 55 and close > ema20_prev:
            return {
                "side": "LONG",
                "reason": f"ADX strong trend ({adx14:.1f}) + RSI pullback ({rsi14:.1f})",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "atr_fixed",
                    "sl_atr_mult": 1.8,
                    "tp_rr_multiple": 2.4,
                    "trail_atr_mult": None,
                    "breakeven_at_R": None
                }
            }
    
    # SHORT
    if close < ind.get('ema200', float('inf')):
        adx14 = ind.get('adx14', 0)
        rsi14 = ind.get('rsi14', 50)
        ema20_prev = ind.get('ema20_prev', float('inf'))
        
        if adx14 >= 25 and 45 <= rsi14 <= 58 and close < ema20_prev:
            return {
                "side": "SHORT",
                "reason": f"ADX strong trend ({adx14:.1f}) + RSI pullback ({rsi14:.1f})",
                "regime_hint": "trend",
                "meta": {
                    "sl_tp_style": "atr_fixed",
                    "sl_atr_mult": 1.8,
                    "tp_rr_multiple": 2.4,
                    "trail_atr_mult": None,
                    "breakeven_at_R": None
                }
            }
    
    return None


TREND_FOLLOWING_STRATEGIES = {
    "trendflow_supertrend": trendflow_supertrend_entry_signal,
    "ema_cloud_trend": ema_cloud_trend_entry_signal,
    "donchian_continuation": donchian_continuation_entry_signal,
    "macd_zero_trend": macd_zero_trend_entry_signal,
    "adx_trend_filter_plus": adx_trend_filter_plus_entry_signal,
}


def get_strategy(name: str):
    """Get strategy function by name"""
    return TREND_FOLLOWING_STRATEGIES.get(name)


def list_strategies():
    """List all available trend following strategies"""
    return list(TREND_FOLLOWING_STRATEGIES.keys())