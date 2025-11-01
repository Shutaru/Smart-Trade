"""
Hybrid / Multi-Factor Strategies (21-25)

Implementation of professional hybrid strategies combining multiple factors:
- Triple momentum confluence (RSI + Stoch + MACD)
- Trend + Volume combination
- EMA stack with momentum confirmation
- Multi-oscillator confluence
- Complete 5-factor system with auto regime detection

Regime: trend, momentum, balanced, auto
"""

from typing import Optional, Dict, Any


def triple_momentum_confluence_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Triple Momentum Confluence
    Category: Hybrid / Momentum
    
    LONG: RSI14>55 + Stoch %K>%D both 40-80 + macd_hist>0 + close>ema50
    SHORT: inverse
    Exits: chandelier, sl=2.0, trail=2.3, tp=2.2
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    ema50 = ind.get('ema50', 0)
    
    rsi14 = ind.get('rsi14', 50)
    stoch_k = ind.get('stoch_k', 50)
    stoch_d = ind.get('stoch_d', 50)
    macd_hist = ind.get('macd_hist', 0)
    
    # LONG: All momentum indicators aligned
    rsi_bullish = rsi14 > 55
    stoch_bullish = stoch_k > stoch_d and 40 <= stoch_k <= 80 and 40 <= stoch_d <= 80
    macd_bullish = macd_hist > 0
    price_above_ema = close > ema50
    
    if rsi_bullish and stoch_bullish and macd_bullish and price_above_ema:
        return {
            "side": "LONG",
            "reason": f"Triple momentum (RSI={rsi14:.1f}, Stoch K={stoch_k:.1f}, MACD={macd_hist:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "chandelier",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.3,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: All momentum indicators aligned bearish
    rsi_bearish = rsi14 < 45
    stoch_bearish = stoch_k < stoch_d and 20 <= stoch_k <= 60 and 20 <= stoch_d <= 60
    macd_bearish = macd_hist < 0
    price_below_ema = close < ema50
    
    if rsi_bearish and stoch_bearish and macd_bearish and price_below_ema:
        return {
            "side": "SHORT",
            "reason": f"Triple momentum down (RSI={rsi14:.1f}, Stoch K={stoch_k:.1f}, MACD={macd_hist:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "chandelier",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.3,
                "breakeven_at_R": None
            }
        }
    
    return None


def trend_volume_combo_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Trend Volume Combo
    Category: Hybrid / Trend + Volume
    
    LONG: supertrend_bull + close>vwap + MFI>50 + ADX>=20
    SHORT: symmetric
    Exits: atr_trailing, sl=1.9, trail=2.1, tp=2.1
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # LONG: Trend + Volume alignment
    supertrend_bull = ind.get('supertrend_bull', False)
    vwap = ind.get('vwap', close)
    mfi = ind.get('mfi', 50)
    adx14 = ind.get('adx14', 0)
    
    long_signal = (
        supertrend_bull and
        close > vwap and
        mfi > 50 and
        adx14 >= 20
    )
    
    if long_signal:
        return {
            "side": "LONG",
            "reason": f"Trend+Volume (ST bull, VWAP support, MFI={mfi:.1f}, ADX={adx14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.9,
                "tp_rr_multiple": 2.1,
                "trail_atr_mult": 2.1,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Trend + Volume alignment bearish
    supertrend_bear = ind.get('supertrend_bear', False)
    
    short_signal = (
        supertrend_bear and
        close < vwap and
        mfi < 50 and
        adx14 >= 20
    )
    
    if short_signal:
        return {
            "side": "SHORT",
            "reason": f"Trend+Volume down (ST bear, VWAP resist, MFI={mfi:.1f}, ADX={adx14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.9,
                "tp_rr_multiple": 2.1,
                "trail_atr_mult": 2.1,
                "breakeven_at_R": None
            }
        }
    
    return None


def ema_stack_momentum_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: EMA Stack Momentum
    Category: Hybrid / Trend
    
    LONG: ema20>ema50>ema200 with positive slopes + pullback to ema20/50 + trigger up
    SHORT: inverted stack
    Exits: breakeven_then_trail, sl=1.8, trail=2.2, tp=2.4, be=1.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    low = bar['low']
    high = bar['high']
    
    ema20 = ind.get('ema20', 0)
    ema50 = ind.get('ema50', 0)
    ema200 = ind.get('ema200', 0)
    
    ema20_prev = ind.get('ema20_prev', 0)
    ema50_prev = ind.get('ema50_prev', 0)
    
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # LONG: EMA stack aligned upward
    stack_bullish = ema20 > ema50 > ema200
    slopes_positive = ema20 > ema20_prev and ema50 > ema50_prev
    pullback = low <= ema20 or low <= ema50
    trigger = close > prev_high
    
    if stack_bullish and slopes_positive and pullback and trigger:
        return {
            "side": "LONG",
            "reason": f"EMA stack momentum (20>{ema20:.2f} 50>{ema50:.2f} 200>{ema200:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.4,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": 1.0
            }
        }
    
    # SHORT: EMA stack aligned downward
    stack_bearish = ema20 < ema50 < ema200
    slopes_negative = ema20 < ema20_prev and ema50 < ema50_prev
    pullback_short = high >= ema20 or high >= ema50
    trigger_short = close < prev_low
    
    if stack_bearish and slopes_negative and pullback_short and trigger_short:
        return {
            "side": "SHORT",
            "reason": f"EMA stack momentum down (20<{ema20:.2f} 50<{ema50:.2f} 200<{ema200:.2f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "breakeven_then_trail",
                "sl_atr_mult": 1.8,
                "tp_rr_multiple": 2.4,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": 1.0
            }
        }
    
    return None


def multi_oscillator_confluence_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Multi-Oscillator Confluence
    Category: Hybrid / Balanced
    
    LONG: RSI14 50-60 + CCI -50->+50 + Stoch %K>%D 40-70 + close>ema50
    SHORT: inverse
    Exits: atr_fixed, sl=1.7, tp=2.0
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    ema50 = ind.get('ema50', 0)
    
    rsi14 = ind.get('rsi14', 50)
    cci = ind.get('cci', 0)
    stoch_k = ind.get('stoch_k', 50)
    stoch_d = ind.get('stoch_d', 50)
    
    # LONG: All oscillators in bullish zone
    rsi_ok = 50 <= rsi14 <= 60
    cci_ok = -50 <= cci <= 50 and cci > 0
    stoch_ok = stoch_k > stoch_d and 40 <= stoch_k <= 70
    price_ok = close > ema50
    
    if rsi_ok and cci_ok and stoch_ok and price_ok:
        return {
            "side": "LONG",
            "reason": f"Multi-oscillator confluence (RSI={rsi14:.1f}, CCI={cci:.1f}, Stoch={stoch_k:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 1.7,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: All oscillators in bearish zone
    rsi_bearish = 40 <= rsi14 <= 50
    cci_bearish = -50 <= cci <= 50 and cci < 0
    stoch_bearish = stoch_k < stoch_d and 30 <= stoch_k <= 60
    price_bearish = close < ema50
    
    if rsi_bearish and cci_bearish and stoch_bearish and price_bearish:
        return {
            "side": "SHORT",
            "reason": f"Multi-oscillator confluence down (RSI={rsi14:.1f}, CCI={cci:.1f}, Stoch={stoch_k:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_fixed",
                "sl_atr_mult": 1.7,
                "tp_rr_multiple": 2.0,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


def complete_system_5x_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: Complete System 5x
    Category: Hybrid / Auto-Regime
    
    LONG: supertrend_bull + RSI14 45-65 + ADX>=20 + VWAP support + ATR non-extreme
    SHORT: symmetric
    Exits: supertrend, sl=2.0, tp=2.3
    
    Auto regime detection based on ADX and volatility
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    supertrend_bull = ind.get('supertrend_bull', False)
    supertrend_bear = ind.get('supertrend_bear', False)
    
    rsi14 = ind.get('rsi14', 50)
    adx14 = ind.get('adx14', 0)
    vwap = ind.get('vwap', close)
    atr_norm_pct = ind.get('atr_norm_pct', 50)
    
    # Auto regime detection
    if adx14 >= 25:
        regime = "trend"
    elif atr_norm_pct >= 70:
        regime = "high_vol"
    elif atr_norm_pct <= 30:
        regime = "low_vol"
    else:
        regime = "range"
    
    # ATR non-extreme (20-80 percentile)
    atr_ok = 20 <= atr_norm_pct <= 80
    
    # LONG: All 5 factors aligned
    long_signal = (
        supertrend_bull and
        45 <= rsi14 <= 65 and
        adx14 >= 20 and
        close > vwap and
        atr_ok
    )
    
    if long_signal:
        return {
            "side": "LONG",
            "reason": f"Complete 5x system (ST+RSI+ADX={adx14:.1f}+VWAP+ATR, regime={regime})",
            "regime_hint": regime,
            "meta": {
                "sl_tp_style": "supertrend",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.3,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: All 5 factors aligned bearish
    short_signal = (
        supertrend_bear and
        35 <= rsi14 <= 55 and
        adx14 >= 20 and
        close < vwap and
        atr_ok
    )
    
    if short_signal:
        return {
            "side": "SHORT",
            "reason": f"Complete 5x system down (ST+RSI+ADX={adx14:.1f}+VWAP+ATR, regime={regime})",
            "regime_hint": regime,
            "meta": {
                "sl_tp_style": "supertrend",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.3,
                "trail_atr_mult": None,
                "breakeven_at_R": None
            }
        }
    
    return None


HYBRID_STRATEGIES = {
    "triple_momentum_confluence": triple_momentum_confluence_entry_signal,
    "trend_volume_combo": trend_volume_combo_entry_signal,
    "ema_stack_momentum": ema_stack_momentum_entry_signal,
    "multi_oscillator_confluence": multi_oscillator_confluence_entry_signal,
    "complete_system_5x": complete_system_5x_entry_signal,
}


def get_strategy(name: str):
    """Get strategy function by name"""
    return HYBRID_STRATEGIES.get(name)


def list_strategies():
    """List all available hybrid strategies"""
    return list(HYBRID_STRATEGIES.keys())