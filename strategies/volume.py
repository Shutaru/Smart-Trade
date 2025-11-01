"""
Volume / Flow Strategies (16-20)

Implementation of professional volume-based strategies with:
- VWAP institutional trend following
- VWAP breakout detection
- MFI momentum impulse
- OBV trend confirmation
- VWAP mean reversion (standard deviation bands)

Regime: trend, range->trend, momentum
"""

from typing import Optional, Dict, Any


def vwap_institutional_trend_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: VWAP Institutional Trend
    Category: Volume / Trend Following
    
    LONG: close>vwap + close>ema200 + MFI>50 + ADX>=20 + pullback to vwap/ema20 with trigger
    SHORT: symmetric
    Exits: breakeven_then_trail, sl=1.9, trail=2.2, tp=2.2, be=1.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    low = bar['low']
    high = bar['high']
    
    vwap = ind.get('vwap', close)
    ema200 = ind.get('ema200', 0)
    ema20 = ind.get('ema20', 0)
    mfi = ind.get('mfi', 50)
    adx14 = ind.get('adx14', 0)
    
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # LONG
    trend_up = close > vwap and close > ema200 and mfi > 50 and adx14 >= 20
    pullback = low <= vwap or low <= ema20
    trigger = close > prev_high
    
    if trend_up and pullback and trigger:
        return {
            "side": "LONG",
            "reason": f"VWAP institutional trend (MFI={mfi:.1f}, ADX={adx14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.9,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": 1.0
            }
        }
    
    # SHORT
    trend_down = close < vwap and close < ema200 and mfi < 50 and adx14 >= 20
    pullback_short = high >= vwap or high >= ema20
    trigger_short = close < prev_low
    
    if trend_down and pullback_short and trigger_short:
        return {
            "side": "SHORT",
            "reason": f"VWAP institutional trend down (MFI={mfi:.1f}, ADX={adx14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.9,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": 1.0
            }
        }
    
    return None


def vwap_breakout_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: VWAP Breakout
    Category: Volume / Breakout
    
    LONG: consolidation near vwap (N bars) + break above prev_high + maintain close>vwap
    SHORT: symmetric below vwap
    Exits: atr_trailing, sl=1.8, trail=2.0, tp=2.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    vwap = ind.get('vwap', close)
    
    # Consolidation detection: close near vwap for recent bars
    # Simplified: check if price is within 1% of vwap
    vwap_consolidation = abs(close - vwap) / vwap < 0.01
    
    # Check previous consolidation (from state or indicator)
    had_consolidation = state.get('vwap_consolidation_bars', 0) >= 3 or vwap_consolidation
    
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # LONG: Break above prev_high while above vwap
    if had_consolidation and close > prev_high and close > vwap:
        return {
            "side": "LONG",
            "reason": f"VWAP breakout from consolidation (close={close:.2f}, vwap={vwap:.2f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Break below prev_low while below vwap
    if had_consolidation and close < prev_low and close < vwap:
        return {
            "side": "SHORT",
            "reason": f"VWAP breakdown from consolidation (close={close:.2f}, vwap={vwap:.2f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": 2.0,
                "breakeven_at_R": None
            }
        }
    
    return None


def mfi_impulse_momentum_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: MFI Impulse Momentum
    Category: Volume / Momentum
    
    LONG: MFI crosses 50->60 + macd_hist>0 + close>ema50
    SHORT: MFI crosses 50->40 + macd_hist<0 + close<ema50
    Exits: atr_fixed, sl=1.8, tp=2.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    ema50 = ind.get('ema50', 0)
    
    mfi = ind.get('mfi', 50)
    mfi_prev = ind.get('mfi_prev', 50)
    macd_hist = ind.get('macd_hist', 0)
    
    # LONG: MFI impulse up (crosses 50 and moves toward 60)
    mfi_impulse_up = mfi_prev <= 50 and mfi >= 50 and mfi <= 60
    
    if mfi_impulse_up and macd_hist > 0 and close > ema50:
        return {
            "side": "LONG",
            "reason": f"MFI impulse momentum up (MFI {mfi_prev:.1f}->{mfi:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: MFI impulse down (crosses 50 and moves toward 40)
    mfi_impulse_down = mfi_prev >= 50 and mfi <= 50 and mfi >= 40
    
    if mfi_impulse_down and macd_hist < 0 and close < ema50:
        return {
            "side": "SHORT",
            "reason": f"MFI impulse momentum down (MFI {mfi_prev:.1f}->{mfi:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


def obv_trend_confirmation_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: OBV Trend Confirmation
    Category: Volume / Trend Following
    
    LONG: OBV making higher highs/higher lows (HH/HL) + long_filters
    SHORT: OBV making lower highs/lower lows (LH/LL) + short_filters
    Exits: supertrend, sl=2.0, tp=2.2
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # Filters
    long_filters = (
        close > ind.get('ema200', 0) and
        ind.get('supertrend_bull', False) and
        ind.get('adx14', 0) >= 18
    )
    
    short_filters = (
        close < ind.get('ema200', float('inf')) and
        ind.get('supertrend_bear', False) and
        ind.get('adx14', 0) >= 18
    )
    
    # OBV trend detection (simplified: compare current vs previous)
    obv = ind.get('obv', 0)
    obv_prev = ind.get('obv_prev', 0)
    obv_5ago = ind.get('obv_5bars_ago', 0)
    
    # LONG: OBV making higher highs/lows
    obv_uptrend = obv > obv_prev and obv > obv_5ago
    
    if obv_uptrend and long_filters:
        return {
            "side": "LONG",
            "reason": f"OBV trend confirmation (OBV rising: {obv_5ago:.0f}->{obv:.0f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "supertrend",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: OBV making lower highs/lows
    obv_downtrend = obv < obv_prev and obv < obv_5ago
    
    if obv_downtrend and short_filters:
        return {
            "side": "SHORT",
            "reason": f"OBV trend confirmation down (OBV falling: {obv_5ago:.0f}->{obv:.0f})",
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


def vwap_mean_reversion_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: VWAP Mean Reversion
    Category: Volume / Mean Reversion
    
    LONG: negative deviation from VWAP (x sigma) + RSI 30-40 + trigger up
    SHORT: positive deviation from VWAP + RSI 60-70
    Exits: keltner, sl=1.6, tp=1.6
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    vwap = ind.get('vwap', close)
    
    # Calculate deviation from VWAP
    # Assuming vwap_std is provided as indicator (standard deviation of price from VWAP)
    vwap_std = ind.get('vwap_std', close * 0.01)  # Default 1% if not available
    
    deviation = (close - vwap) / vwap_std if vwap_std > 0 else 0
    
    rsi14 = ind.get('rsi14', 50)
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # LONG: Negative deviation (oversold vs VWAP)
    negative_deviation = deviation < -1.5  # More than 1.5 std below VWAP
    
    if negative_deviation and 30 <= rsi14 <= 40 and close > prev_high:
        return {
            "side": "LONG",
            "reason": f"VWAP mean reversion (dev={deviation:.2f}σ, RSI={rsi14:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "keltner",
                "sl_atr_mult": 1.6,
                "tp_rr_multiple": 1.6,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Positive deviation (overbought vs VWAP)
    positive_deviation = deviation > 1.5  # More than 1.5 std above VWAP
    
    if positive_deviation and 60 <= rsi14 <= 70 and close < prev_low:
        return {
            "side": "SHORT",
            "reason": f"VWAP mean reversion (dev={deviation:.2f}σ, RSI={rsi14:.1f})",
            "regime_hint": "range",
            "meta": {
                "sl_tp_style": "keltner",
                "sl_atr_mult": 1.6,
                "tp_rr_multiple": 1.6,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


VOLUME_STRATEGIES = {
    "vwap_institutional_trend": vwap_institutional_trend_entry_signal,
    "vwap_breakout": vwap_breakout_entry_signal,
    "mfi_impulse_momentum": mfi_impulse_momentum_entry_signal,
    "obv_trend_confirmation": obv_trend_confirmation_entry_signal,
    "vwap_mean_reversion": vwap_mean_reversion_entry_signal,
}


def get_strategy(name: str):
    """Get strategy function by name"""
    return VOLUME_STRATEGIES.get(name)


def list_strategies():
    """List all available volume strategies"""
    return list(VOLUME_STRATEGIES.keys())