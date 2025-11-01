"""
Indicator Adapter - Bridge between features.py and strategy format

Converts the existing indicator system to the format expected by the 38 strategies.

The 38 strategies expect indicators in a specific format:
    ind = {
        'ema20': value,
        'ema50': value,
        'rsi14': value,
        'supertrend_bull': bool,
        ...
        'prev_high': value,
        'close_prev': value,
        etc.
    }

This adapter takes the output from features.py and transforms it.
"""

from typing import Dict, Any, List
import numpy as np


def build_indicator_dict(i: int, ts: List, o: List, h: List, l: List, c: List, feats: Dict) -> Dict[str, Any]:
    """
    Build indicator dictionary for a specific bar index
    
    Args:
        i: Current bar index
        ts: Timestamp array
        o: Open array
        h: High array
        l: Low array
        c: Close array
        feats: Features dictionary from compute_feature_rows
        
    Returns:
        Dictionary with all indicators in the format expected by strategies
    """
    
    # Helper to safely get value from array
    def get_val(arr, idx, default=None):
        try:
            if arr is None or idx < 0 or idx >= len(arr):
                return default
            val = arr[idx]
            return val if val is not None and not (isinstance(val, float) and np.isnan(val)) else default
        except (IndexError, TypeError):
            return default
    
    # Helper to safely get previous value
    def get_prev(arr, idx, default=None):
        return get_val(arr, idx - 1, default) if idx > 0 else default
    
    # Helper to get value N bars ago
    def get_ago(arr, idx, n, default=None):
        return get_val(arr, idx - n, default) if idx >= n else default
    
    ind = {}
    
    # ========================================================================
    # PRICE DATA
    # ========================================================================
    ind['close'] = get_val(c, i, 0)
    ind['open'] = get_val(o, i, 0)
    ind['high'] = get_val(h, i, 0)
    ind['low'] = get_val(l, i, 0)
    
    # Previous values
    ind['close_prev'] = get_prev(c, i, ind['close'])
    ind['open_prev'] = get_prev(o, i, ind['open'])
    ind['high_prev'] = get_prev(h, i, ind['high'])
    ind['low_prev'] = get_prev(l, i, ind['low'])
    
    # Previous high/low (for breakout detection)
    ind['prev_high'] = get_prev(h, i, ind['high'])
    ind['prev_low'] = get_prev(l, i, ind['low'])
    
    # ========================================================================
    # TREND INDICATORS
    # ========================================================================
    
    # EMAs
    ind['ema20'] = get_val(feats.get('ema20'), i, ind['close'])
    ind['ema50'] = get_val(feats.get('ema50'), i, ind['close'])
    ind['ema200'] = get_val(feats.get('ema200'), i, ind['close'])
    
    ind['ema20_prev'] = get_prev(feats.get('ema20'), i, ind['ema20'])
    ind['ema50_prev'] = get_prev(feats.get('ema50'), i, ind['ema50'])
    
    # SMAs (if available)
    ind['sma20'] = get_val(feats.get('sma20'), i, ind['close'])
    ind['sma50'] = get_val(feats.get('sma50'), i, ind['close'])
    ind['sma200'] = get_val(feats.get('sma200'), i, ind['close'])
    
    # SuperTrend
    st_line = get_val(feats.get('supertrend'), i, ind['close'])
    st_dir = get_val(feats.get('supertrend_dir'), i, 1)
    
    ind['supertrend'] = st_line
    ind['supertrend_bull'] = st_dir == 1
    ind['supertrend_bear'] = st_dir == -1
    
    # Previous SuperTrend
    st_dir_prev = get_prev(feats.get('supertrend_dir'), i, st_dir)
    ind['supertrend_bull_prev'] = st_dir_prev == 1
    ind['supertrend_bear_prev'] = st_dir_prev == -1
    
    # ========================================================================
    # MOMENTUM INDICATORS
    # ========================================================================
    
    # RSI
    ind['rsi14'] = get_val(feats.get('rsi14'), i, 50)
    ind['rsi5'] = get_val(feats.get('rsi5'), i, 50)
    ind['rsi7'] = get_val(feats.get('rsi7'), i, 50)
    ind['rsi_14'] = ind['rsi14']  # Alias
    
    ind['rsi14_prev'] = get_prev(feats.get('rsi14'), i, ind['rsi14'])
    
    # Stochastic
    ind['stoch_k'] = get_val(feats.get('stoch_k'), i, 50)
    ind['stoch_d'] = get_val(feats.get('stoch_d'), i, 50)
    
    ind['stoch_k_prev'] = get_prev(feats.get('stoch_k'), i, ind['stoch_k'])
    ind['stoch_d_prev'] = get_prev(feats.get('stoch_d'), i, ind['stoch_d'])
    
    # MACD
    ind['macd'] = get_val(feats.get('macd'), i, 0)
    ind['macd_signal'] = get_val(feats.get('macd_signal'), i, 0)
    ind['macd_hist'] = get_val(feats.get('macd_hist'), i, 0)
    
    # CCI
    ind['cci'] = get_val(feats.get('cci20'), i, 0)
    ind['cci_prev'] = get_prev(feats.get('cci20'), i, ind['cci'])
    
    # Williams %R
    ind['williams_r'] = get_val(feats.get('williams_r'), i, -50)
    
    # ADX
    ind['adx14'] = get_val(feats.get('adx14'), i, 0)
    ind['adx14_prev'] = get_prev(feats.get('adx14'), i, ind['adx14'])
    ind['adx14_5bars_ago'] = get_ago(feats.get('adx14'), i, 5, ind['adx14'])
    
    # ========================================================================
    # VOLATILITY INDICATORS
    # ========================================================================
    
    # ATR
    ind['atr'] = get_val(feats.get('atr14'), i, ind['close'] * 0.01)
    ind['atr14'] = ind['atr']  # Alias
    
    # ATR percentile (if available)
    ind['atr_norm_pct'] = get_val(feats.get('atr1h_pct'), i, 50)
    
    # Bollinger Bands
    ind['bb_upper'] = get_val(feats.get('bb_up'), i, ind['close'] * 1.02)
    ind['bb_middle'] = get_val(feats.get('bb_mid'), i, ind['close'])
    ind['bb_lower'] = get_val(feats.get('bb_lo'), i, ind['close'] * 0.98)
    
    # BB bandwidth percentage
    bb_width = ind['bb_upper'] - ind['bb_lower']
    ind['bb_bw_pct'] = (bb_width / ind['bb_middle'] * 100) if ind['bb_middle'] > 0 else 100
    ind['bb_bw_pct_prev'] = get_prev(feats.get('bb_bw_pct'), i, ind['bb_bw_pct']) if 'bb_bw_pct' in feats else ind['bb_bw_pct']
    
    # Keltner Channels
    ind['keltner_upper'] = get_val(feats.get('keltner_up'), i, ind['close'] * 1.02)
    ind['keltner_mid'] = get_val(feats.get('keltner_mid'), i, ind['close'])
    ind['keltner_lower'] = get_val(feats.get('keltner_lo'), i, ind['close'] * 0.98)
    
    # BB inside Keltner (squeeze detection)
    ind['boll_in_keltner'] = (
        ind['bb_upper'] < ind['keltner_upper'] and
        ind['bb_lower'] > ind['keltner_lower']
    )
    
    # Donchian Channels
    ind['donchian_high20'] = get_val(feats.get('up55'), i, ind['high'])  # Using dn55/up55 as Donchian
    ind['donchian_low20'] = get_val(feats.get('dn55'), i, ind['low'])
    ind['donchian_middle'] = (ind['donchian_high20'] + ind['donchian_low20']) / 2
    
    # Donchian 10-period (if available)
    ind['donchian_high10'] = get_val(feats.get('donchian_high10'), i, ind['donchian_high20'])
    ind['donchian_low10'] = get_val(feats.get('donchian_low10'), i, ind['donchian_low20'])
    
    # ========================================================================
    # VOLUME INDICATORS
    # ========================================================================
    
    # VWAP
    ind['vwap'] = get_val(feats.get('vwap'), i, ind['close'])
    
    # VWAP standard deviation (estimated)
    ind['vwap_std'] = ind['atr'] * 0.5  # Rough estimate if not available
    
    # OBV
    ind['obv'] = get_val(feats.get('obv'), i, 0)
    ind['obv_prev'] = get_prev(feats.get('obv'), i, ind['obv'])
    ind['obv_5bars_ago'] = get_ago(feats.get('obv'), i, 5, ind['obv'])
    
    # MFI
    ind['mfi'] = get_val(feats.get('mfi14'), i, 50)
    ind['mfi_prev'] = get_prev(feats.get('mfi14'), i, ind['mfi'])
    ind['mfi_5bars_ago'] = get_ago(feats.get('mfi14'), i, 5, ind['mfi'])
    
    # ========================================================================
    # REGIME / SESSION (placeholders - needs implementation)
    # ========================================================================
    
    ind['regime'] = get_val(feats.get('regime'), i, 'NEUTRAL')
    
    # Session detection (placeholder - needs proper implementation)
    ind['is_london_session'] = False  # TODO: Implement based on timestamp
    ind['is_ny_session'] = False
    ind['minutes_since_ny_open'] = 999
    
    # Opening range (placeholder)
    ind['or_high'] = ind['high']
    ind['or_low'] = ind['low']
    
    return ind


def build_bar_dict(i: int, o: List, h: List, l: List, c: List, v: List = None) -> Dict[str, float]:
    """
    Build bar dictionary for current candle
    
    Args:
        i: Current bar index
        o: Open array
        h: High array
        l: Low array
        c: Close array
        v: Volume array (optional)
        
    Returns:
        Dictionary with OHLCV data
    """
    bar = {
        'open': o[i] if i < len(o) else 0,
        'high': h[i] if i < len(h) else 0,
        'low': l[i] if i < len(l) else 0,
        'close': c[i] if i < len(c) else 0,
    }
    
    if v is not None and i < len(v):
        bar['volume'] = v[i]
    
    return bar


def build_state_dict(position=None, cooldown_bars_left=0, **kwargs) -> Dict[str, Any]:
    """
    Build state dictionary for strategy execution
    
    Args:
        position: Current position (None if flat, 'LONG' or 'SHORT')
        cooldown_bars_left: Remaining cooldown bars after stop
        **kwargs: Additional state variables
    
    Returns:
        Dictionary with state information
    """
    state = {
        'position': position,
        'cooldown_bars_left': cooldown_bars_left,
    }
    
    # Add any additional state
    state.update(kwargs)
    
    return state


def extract_exit_params(signal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract exit parameters from strategy signal
    
    Args:
        signal: Strategy signal dictionary with 'meta' field
        
    Returns:
        Dictionary with exit parameters for broker
    """
    if not signal or 'meta' not in signal:
        return {}
    
    meta = signal['meta']
    
    exit_params = {
        'sl_tp_style': meta.get('sl_tp_style', 'atr_fixed'),
        'sl_atr_mult': meta.get('sl_atr_mult', 2.0),
        'tp_rr_multiple': meta.get('tp_rr_multiple', 2.0),
        'trail_atr_mult': meta.get('trail_atr_mult'),
        'breakeven_at_R': meta.get('breakeven_at_R'),
    }
    
    return exit_params


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("Indicator Adapter - Usage Example")
    print("=" * 80)
    print("""
# In your backtest loop:

from indicator_adapter import build_indicator_dict, build_bar_dict, build_state_dict
from strategy_registry import get_strategy

# Get strategy
strategy_fn = get_strategy("trendflow_supertrend")

# Build inputs
bar = build_bar_dict(i, o, h, l, c, v)
ind = build_indicator_dict(i, ts, o, h, l, c, feats)
state = build_state_dict(position=None, cooldown_bars_left=0)
params = {}  # Strategy-specific parameters

# Get signal
signal = strategy_fn(bar, ind, state, params)

if signal:
    print(f"Side: {signal['side']}")
    print(f"Reason: {signal['reason']}")
    print(f"Regime: {signal['regime_hint']}")
    print(f"Exit style: {signal['meta']['sl_tp_style']}")
    """)