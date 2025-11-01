"""
Regime Detection for Exit Plan Adaptation

Detects market regime to adapt exit parameters:
- TREND: ADX >= 25, price trending
- RANGE: ADX < 20, Bollinger squeeze
- HIGH_VOL: ATR in top 20% of recent range
- LOW_VOL: ATR in bottom 20% of recent range
"""

from typing import List, Literal, Optional
import numpy as np

RegimeType = Literal["trend", "range", "high_vol", "low_vol"]


class RegimeDetector:
    """
    Detect market regime using ADX, ATR, and Bollinger Bands
    """
    
    def __init__(self, lookback_bars: int = 100):
        self.lookback_bars = lookback_bars
    
    def detect(
        self,
        adx: List[float],
        atr: List[float],
        close: List[float],
        ema200: Optional[List[float]] = None,
        bb_upper: Optional[List[float]] = None,
        bb_lower: Optional[List[float]] = None,
        bb_middle: Optional[List[float]] = None,
        current_idx: int = -1
    ) -> RegimeType:
        """
        Detect current market regime
        
        Args:
            adx: ADX values
            atr: ATR values
            close: Close prices
            ema200: EMA200 values (optional, for trend confirmation)
            bb_upper: Bollinger upper band (optional, for squeeze detection)
            bb_lower: Bollinger lower band (optional, for squeeze detection)
            bb_middle: Bollinger middle band (optional)
            current_idx: Index to check (-1 for last)
        
        Returns:
            RegimeType: "trend", "range", "high_vol", or "low_vol"
        """
        
        if current_idx < 0:
            current_idx = len(adx) + current_idx
        
        if current_idx < 0 or current_idx >= len(adx):
            return "range"  # Default safe mode
        
        # Get current values
        current_adx = adx[current_idx]
        current_atr = atr[current_idx]
        current_close = close[current_idx]
        
        # === Volatility Check ===
        # Calculate ATR percentile in recent history
        start_idx = max(0, current_idx - self.lookback_bars)
        recent_atr = atr[start_idx:current_idx + 1]
        
        if len(recent_atr) > 10:
            atr_percentile = self._calculate_percentile(current_atr, recent_atr)
            
            if atr_percentile >= 80:
                return "high_vol"
            elif atr_percentile <= 20:
                return "low_vol"
        
        # === Trend vs Range ===
        # Strong trend: ADX >= 25
        if current_adx >= 25:
            # Confirm with EMA200 if available
            if ema200 and current_idx < len(ema200):
                ema = ema200[current_idx]
                if abs(current_close - ema) / ema > 0.02:  # 2% away from EMA200
                    return "trend"
            else:
                return "trend"
        
        # Range: ADX < 20
        if current_adx < 20:
            # Check for Bollinger squeeze
            if bb_upper and bb_lower and current_idx < len(bb_upper):
                bb_up = bb_upper[current_idx]
                bb_lo = bb_lower[current_idx]
                bb_mid = bb_middle[current_idx] if bb_middle else (bb_up + bb_lo) / 2
                
                # Squeeze: bands are tight
                bandwidth = (bb_up - bb_lo) / bb_mid if bb_mid > 0 else 0
                
                # Historical bandwidth for comparison
                start_idx = max(0, current_idx - self.lookback_bars)
                historical_bw = []
                for i in range(start_idx, current_idx):
                    if i < len(bb_upper):
                        up = bb_upper[i]
                        lo = bb_lower[i]
                        mid = bb_middle[i] if bb_middle else (up + lo) / 2
                        if mid > 0:
                            historical_bw.append((up - lo) / mid)
                
                if historical_bw:
                    avg_bw = np.mean(historical_bw)
                    if bandwidth < avg_bw * 0.7:  # 30% tighter than average
                        return "range"
            
            return "range"
        
        # Default: range (neutral state)
        return "range"
    
    def _calculate_percentile(self, value: float, values: List[float]) -> float:
        """Calculate percentile rank of value in list"""
        if not values or len(values) < 2:
            return 50.0
        
        sorted_values = sorted(values)
        rank = sum(1 for v in sorted_values if v <= value)
        return (rank / len(sorted_values)) * 100
    
    def detect_simple(
        self,
        adx_current: float,
        atr_current: float,
        atr_history: List[float],
        close_current: float,
        ema200_current: Optional[float] = None
    ) -> RegimeType:
        """
        Simplified regime detection using current values only
        
        Args:
            adx_current: Current ADX value
            atr_current: Current ATR value
            atr_history: Recent ATR history for percentile calc
            close_current: Current close price
            ema200_current: Current EMA200 (optional)
        
        Returns:
            RegimeType
        """
        
        # Volatility percentile
        if len(atr_history) > 10:
            atr_pct = self._calculate_percentile(atr_current, atr_history)
            
            if atr_pct >= 80:
                return "high_vol"
            elif atr_pct <= 20:
                return "low_vol"
        
        # Trend check
        if adx_current >= 25:
            if ema200_current:
                if abs(close_current - ema200_current) / ema200_current > 0.02:
                    return "trend"
            else:
                return "trend"
        
        # Range check
        if adx_current < 20:
            return "range"
        
        # Default
        return "range"


def get_swing_levels(
    high: List[float],
    low: List[float],
    lookback: int = 20,
    current_idx: int = -1
) -> tuple[Optional[float], Optional[float]]:
    """
    Find recent swing high and swing low
    
    Args:
        high: High prices
        low: Low prices
        lookback: Bars to look back
        current_idx: Current index (-1 for last)
    
    Returns:
        (swing_low, swing_high) or (None, None)
    """
    
    if current_idx < 0:
        current_idx = len(high) + current_idx
    
    if current_idx < lookback:
        return (None, None)
    
    start_idx = current_idx - lookback
    
    recent_highs = high[start_idx:current_idx + 1]
    recent_lows = low[start_idx:current_idx + 1]
    
    if not recent_highs or not recent_lows:
        return (None, None)
    
    swing_high = max(recent_highs)
    swing_low = min(recent_lows)
    
    return (swing_low, swing_high)


def build_context(
    high: float,
    low: float,
    close: float,
    highest_since_entry: float,
    lowest_since_entry: float,
    swing_low: Optional[float] = None,
    swing_high: Optional[float] = None,
    supertrend: Optional[float] = None,
    keltner_upper: Optional[float] = None,
    keltner_lower: Optional[float] = None,
    tick_size: float = 0.01
) -> dict:
    """
    Build context dict for exit plan
    
    Args:
        high: Current high
        low: Current low
        close: Current close
        highest_since_entry: Highest price since entry
        lowest_since_entry: Lowest price since entry
        swing_low: Recent swing low (optional)
        swing_high: Recent swing high (optional)
        supertrend: SuperTrend value (optional)
        keltner_upper: Keltner upper band (optional)
        keltner_lower: Keltner lower band (optional)
        tick_size: Minimum price increment
    
    Returns:
        Context dict for exit plan
    """
    
    ctx = {
        "high": high,
        "low": low,
        "close": close,
        "highest_since_entry": highest_since_entry,
        "lowest_since_entry": lowest_since_entry,
        "tick_size": tick_size
    }
    
    if swing_low is not None:
        ctx["swing_low"] = swing_low
    
    if swing_high is not None:
        ctx["swing_high"] = swing_high
    
    if supertrend is not None:
        ctx["supertrend"] = supertrend
    
    if keltner_upper is not None:
        ctx["keltner_up"] = keltner_upper
    
    if keltner_lower is not None:
        ctx["keltner_lo"] = keltner_lower
    
    return ctx