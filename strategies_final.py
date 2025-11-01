"""
Final Strategies (36-38) - Completing the 38-Strategy System

Implementation of the final professional strategies:
- VWAP band fade PRO (advanced mean reversion with filters)
- OBV confirmation breakout PLUS (volume + breakout)
- EMA stack regime flip (golden/death cross detection)

These complete the comprehensive 38-strategy trading system.

Regime: range, breakout, trend
"""

from typing import Optional, Dict, Any


def vwap_band_fade_pro_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: VWAP Band Fade PRO
    Category: Mean Reversion / Advanced
    
    LONG: -X sigma from VWAP + BB lower confluence + MFI>=40 + trigger up
          Block if ADX>=25 (avoid trending markets)
    SHORT: +X sigma from VWAP + BB upper + MFI<=60
           Block in high trend
    Exits: keltner, sl=1.6, tp=1.6
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # VWAP deviation calculation
    vwap = ind.get('vwap', close)
    vwap_std = ind.get('vwap_std', close * 0.01)  # Standard deviation
    
    deviation = (close - vwap) / vwap_std if vwap_std > 0 else 0
    sigma_threshold = params.get('vwap_sigma_threshold', 1.5)
    
    # Bollinger Bands
    bb_lower = ind.get('bb_lower', 0)
    bb_upper = ind.get('bb_upper', float('inf'))
    
    # MFI and ADX
    mfi = ind.get('mfi', 50)
    adx14 = ind.get('adx14', 0)
    adx_threshold = params.get('adx_trend_block', 25)
    
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # LONG: Negative deviation (oversold) - BLOCK if trending
    if adx14 >= adx_threshold:
        # Skip LONG in strong trend (avoid catching falling knife)
        pass
    else:
        negative_dev = deviation < -sigma_threshold
        bb_confluence = close <= bb_lower * 1.01
        mfi_ok = mfi >= 40  # Volume not extremely bearish
        trigger = close > prev_high
        
        if negative_dev and bb_confluence and mfi_ok and trigger:
            return {
                "side": "LONG",
                "reason": f"VWAP fade PRO (dev={deviation:.2f}σ, MFI={mfi:.1f}, ADX={adx14:.1f})",
                "regime_hint": "range",
                "meta": {
                    "sl_tp_style": "keltner",
                    "sl_atr_mult": 1.6,
                    "tp_rr_multiple": 1.6,
                    "trail_atr_mult": None,
                    "breakeven_at_R": None
                }
            }
    
    # SHORT: Positive deviation (overbought) - BLOCK if trending
    if adx14 >= adx_threshold:
        # Skip SHORT in strong trend
        pass
    else:
        positive_dev = deviation > sigma_threshold
        bb_confluence_short = close >= bb_upper * 0.99
        mfi_ok_short = mfi <= 60  # Volume not extremely bullish
        trigger_short = close < prev_low
        
        if positive_dev and bb_confluence_short and mfi_ok_short and trigger_short:
            return {
                "side": "SHORT",
                "reason": f"VWAP fade PRO down (dev={deviation:.2f}σ, MFI={mfi:.1f}, ADX={adx14:.1f})",
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


def obv_confirmation_breakout_plus_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: OBV Confirmation Breakout PLUS
    Category: Volume / Breakout
    
    LONG: OBV making HH/HL (N bars) + close>keltner_upper + ADX rising
    SHORT: OBV making LH/LL + close<keltner_lower
    Exits: chandelier, sl=2.0, trail=2.3, tp=2.2
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # OBV trend detection
    obv = ind.get('obv', 0)
    obv_prev = ind.get('obv_prev', 0)
    obv_5ago = ind.get('obv_5bars_ago', 0)
    obv_lookback = params.get('obv_lookback_bars', 10)
    
    # Simplified HH/HL detection (bullish OBV trend)
    obv_hh = obv > obv_prev and obv > obv_5ago
    
    # Simplified LH/LL detection (bearish OBV trend)
    obv_ll = obv < obv_prev and obv < obv_5ago
    
    # Keltner breakout
    keltner_upper = ind.get('keltner_upper', float('inf'))
    keltner_lower = ind.get('keltner_lower', 0)
    
    # ADX momentum
    adx14 = ind.get('adx14', 0)
    adx14_prev = ind.get('adx14_prev', 0)
    adx_rising = adx14 > adx14_prev
    
    # LONG: OBV bullish + Keltner breakout + ADX rising
    if obv_hh and close > keltner_upper and adx_rising:
        return {
            "side": "LONG",
            "reason": f"OBV breakout confirmation (OBV {obv_5ago:.0f}->{obv:.0f}, ADX {adx14_prev:.1f}->{adx14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "chandelier",
                "sl_atr_mult": 2.0,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.3,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: OBV bearish + Keltner breakdown + ADX rising
    if obv_ll and close < keltner_lower and adx_rising:
        return {
            "side": "SHORT",
            "reason": f"OBV breakdown confirmation (OBV {obv_5ago:.0f}->{obv:.0f}, ADX {adx14_prev:.1f}->{adx14:.1f})",
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


def ema_stack_regime_flip_entry_signal(bar: Dict, ind: Dict, state: Dict, params: Dict) -> Optional[Dict]:
    """
    Strategy: EMA Stack Regime Flip
    Category: Trend / Golden/Death Cross
    
    LONG: EMA20 crosses above EMA50 + both > EMA200 + RSI14>50 + break prev_high
    SHORT: EMA20 crosses below EMA50 + RSI14<50
    Exits: atr_trailing, sl=1.9, trail=2.2, tp=2.2
    
    This detects the classic "Golden Cross" (bullish) and "Death Cross" (bearish)
    """
    if state.get("cooldown_bars_left", 0) > 0:
        return None
    
    close = bar['close']
    
    # EMA values
    ema20 = ind.get('ema20', 0)
    ema50 = ind.get('ema50', 0)
    ema200 = ind.get('ema200', 0)
    
    ema20_prev = ind.get('ema20_prev', 0)
    ema50_prev = ind.get('ema50_prev', 0)
    
    # RSI
    rsi14 = ind.get('rsi14', 50)
    
    # Triggers
    prev_high = ind.get('prev_high', float('inf'))
    prev_low = ind.get('prev_low', 0)
    
    # LONG: Golden Cross detection (EMA20 crosses above EMA50)
    golden_cross = ema20_prev <= ema50_prev and ema20 > ema50
    both_above_200 = ema20 > ema200 and ema50 > ema200
    rsi_bullish = rsi14 > 50
    trigger = close > prev_high
    
    if golden_cross and both_above_200 and rsi_bullish and trigger:
        return {
            "side": "LONG",
            "reason": f"Golden Cross (EMA20 crossed EMA50, RSI={rsi14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.9,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": None
            }
        }
    
    # SHORT: Death Cross detection (EMA20 crosses below EMA50)
    death_cross = ema20_prev >= ema50_prev and ema20 < ema50
    both_below_200 = ema20 < ema200 and ema50 < ema200
    rsi_bearish = rsi14 < 50
    trigger_short = close < prev_low
    
    if death_cross and both_below_200 and rsi_bearish and trigger_short:
        return {
            "side": "SHORT",
            "reason": f"Death Cross (EMA20 crossed below EMA50, RSI={rsi14:.1f})",
            "regime_hint": "trend",
            "meta": {
                "sl_tp_style": "atr_trailing",
                "sl_atr_mult": 1.9,
                "tp_rr_multiple": 2.2,
                "trail_atr_mult": 2.2,
                "breakeven_at_R": None
            }
        }
    
    return None


FINAL_STRATEGIES = {
    "vwap_band_fade_pro": vwap_band_fade_pro_entry_signal,
    "obv_confirmation_breakout_plus": obv_confirmation_breakout_plus_entry_signal,
    "ema_stack_regime_flip": ema_stack_regime_flip_entry_signal,
}


def get_strategy(name: str):
    """Get strategy function by name"""
    return FINAL_STRATEGIES.get(name)


def list_strategies():
    """List all available final strategies"""
    return list(FINAL_STRATEGIES.keys())