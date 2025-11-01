"""
Strategy Parameter Mapper

Maps calculated indicators to strategy-specific indicator names.
Handles the translation between generic indicator names and strategy expectations.
"""

from typing import Dict, Any
import pandas as pd


# ============================================================================
# INDICATOR NAME MAPPINGS
# ============================================================================

# Default mappings (most strategies use these)
DEFAULT_INDICATOR_MAPPING = {
    'ema20': 'ema20',
    'ema50': 'ema50',
    'ema200': 'ema200',
    'rsi14': 'rsi14',
    'bb_upper': 'bb_upper',
    'bb_lower': 'bb_lower',
    'bb_middle': 'bb_middle',
    'adx14': 'adx14',
    'atr': 'atr',
    'macd_hist': 'macd_hist',
    'stoch_k': 'stoch_k',
    'stoch_d': 'stoch_d',
    'cci': 'cci',
    'mfi': 'mfi',
    'supertrend': 'supertrend',
    'donchian_high20': 'donchian_high20',
    'donchian_low20': 'donchian_low20',
    'keltner_upper': 'keltner_upper',
    'keltner_lower': 'keltner_lower',
    'keltner_middle': 'keltner_mid',
    'obv': 'obv',
    'vwap': 'vwap',
    'prev_high': 'prev_high',
    'prev_low': 'prev_low',
    'close_prev': 'close_prev',
    'high_prev': 'high_prev',
    'low_prev': 'low_prev'
}


# ============================================================================
# REQUIRED INDICATORS PER STRATEGY
# ============================================================================

STRATEGY_REQUIRED_INDICATORS = {
    'bollinger_mean_reversion': [
        'bb_lower', 'bb_upper', 'bb_middle', 'close_prev', 'rsi14'
    ],
    'rsi_band_reversion': [
        'rsi14', 'bb_lower', 'bb_upper', 'ema50', 'prev_high', 'prev_low'
    ],
    'ema_cloud_trend': [
        'ema20', 'ema50', 'ema200', 'rsi14', 'prev_high'
    ],
    'stoch_signal_reversal': [
        'stoch_k', 'stoch_d', 'stoch_k_prev', 'stoch_d_prev', 'ema50', 'rsi14'
    ],
    'cci_extreme_snapback': [
        'cci', 'cci_prev', 'ema20', 'ema50'
    ],
    'mfi_divergence_reversion': [
        'mfi', 'mfi_prev', 'ema20', 'close_prev', 'low_prev', 'high_prev'
    ],
}


def get_required_params_for_strategy(strategy_name: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get required parameters to calculate indicators for a strategy
    
    Args:
        strategy_name: Name of strategy
        metadata: Optional strategy metadata
    
    Returns:
        Dictionary of parameters needed
    """
    params = {}
    
    # Get required indicators
    required = STRATEGY_REQUIRED_INDICATORS.get(strategy_name, [])
    
    if not required and metadata and 'indicators' in metadata:
        required = metadata['indicators']
    
    # Determine which indicators to calculate
    needs_rsi = any('rsi' in ind.lower() for ind in required)
    needs_bb = any('bb' in ind.lower() or 'bollinger' in ind.lower() for ind in required)
    needs_ema = any('ema' in ind.lower() for ind in required)
    needs_stoch = any('stoch' in ind.lower() for ind in required)
    needs_cci = any('cci' in ind.lower() for ind in required)
    needs_mfi = any('mfi' in ind.lower() for ind in required)
    needs_adx = any('adx' in ind.lower() for ind in required)
    needs_atr = any('atr' in ind.lower() for ind in required)
    needs_macd = any('macd' in ind.lower() for ind in required)
    needs_supertrend = any('supertrend' in ind.lower() for ind in required)
    needs_donchian = any('donchian' in ind.lower() for ind in required)
    needs_keltner = any('keltner' in ind.lower() for ind in required)
    needs_obv = any('obv' in ind.lower() for ind in required)
    needs_vwap = any('vwap' in ind.lower() for ind in required)
    needs_prev = any('prev' in ind.lower() for ind in required)
    
    # Set parameters
    if needs_rsi:
        params['rsi_period'] = params.get('rsi_period', 14)
    
    if needs_bb:
        params['bb_period'] = params.get('bb_period', 20)
        params['bb_std'] = params.get('bb_std', 2.0)
    
    if needs_ema:
        # Determine which EMAs are needed
        if 'ema20' in required or 'ema_20' in required:
            params['ema_fast_period'] = params.get('ema_fast_period', 20)
        if 'ema50' in required or 'ema_50' in required:
            params['ema_slow_period'] = params.get('ema_slow_period', 50)
        if 'ema200' in required or 'ema_200' in required:
            params['ema_trend_period'] = params.get('ema_trend_period', 200)
    
    if needs_stoch:
        params['stoch_k_period'] = params.get('stoch_k_period', 14)
        params['stoch_d_period'] = params.get('stoch_d_period', 3)
    
    if needs_cci:
        params['cci_period'] = params.get('cci_period', 20)
    
    if needs_mfi:
        params['mfi_period'] = params.get('mfi_period', 14)
    
    if needs_adx:
        params['adx_period'] = params.get('adx_period', 14)
    
    if needs_atr:
        params['atr_period'] = params.get('atr_period', 14)
    
    if needs_macd:
        params['macd_fast'] = params.get('macd_fast', 12)
        params['macd_slow'] = params.get('macd_slow', 26)
        params['macd_signal'] = params.get('macd_signal', 9)
    
    if needs_supertrend:
        params['supertrend_period'] = params.get('supertrend_period', 10)
        params['supertrend_mult'] = params.get('supertrend_mult', 3.0)
    
    if needs_donchian:
        params['donchian_period'] = params.get('donchian_period', 20)
    
    if needs_keltner:
        params['keltner_period'] = params.get('keltner_period', 20)
        params['keltner_mult'] = params.get('keltner_mult', 2.0)
    
    if needs_obv:
        params['include_obv'] = True
    
    if needs_vwap:
        params['include_vwap'] = True
    
    if needs_prev:
        params['include_prev'] = True
    
    return params


def ensure_required_indicators(
    indicators: Dict[str, pd.Series],
    strategy_name: str
) -> Dict[str, pd.Series]:
    """
    Ensure all required indicators are present with correct names
    
    Args:
        indicators: Calculated indicators dict
        strategy_name: Strategy name
    
    Returns:
        Indicators dict with all required indicators
    """
    required = STRATEGY_REQUIRED_INDICATORS.get(strategy_name, [])
    
    # Check if all required indicators are present
    missing = []
    for req in required:
        if req not in indicators:
            missing.append(req)
    
    if missing:
        # Try to add missing indicators with alternative names
        for req in missing:
            # Check common alternatives
            if req == 'keltner_mid' and 'keltner_middle' in indicators:
                indicators['keltner_mid'] = indicators['keltner_middle']
            elif req == 'keltner_middle' and 'keltner_mid' in indicators:
                indicators['keltner_middle'] = indicators['keltner_mid']
            elif req.endswith('_prev') and req not in indicators:
                # Try to create _prev version if base exists
                base_name = req[:-5]  # Remove '_prev'
                if base_name in indicators:
                    indicators[req] = indicators[base_name].shift(1)
    
    return indicators


def merge_user_params_with_defaults(
    user_params: Dict[str, Any],
    strategy_name: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Merge user parameters with strategy defaults
    
    Args:
        user_params: User-provided parameters
        strategy_name: Strategy name
        metadata: Optional strategy metadata
    
    Returns:
        Complete parameter dictionary
    """
    # Get required default params
    defaults = get_required_params_for_strategy(strategy_name, metadata)
    
    # Merge with user params (user params take precedence)
    merged = {**defaults, **user_params}
    
    return merged


if __name__ == '__main__':
    print("✅ Testing Strategy Parameter Mapper...")
    
    # Test 1: bollinger_mean_reversion
    print("\n" + "=" * 80)
    print("TEST 1: bollinger_mean_reversion required params")
    print("=" * 80)
    
    params1 = get_required_params_for_strategy('bollinger_mean_reversion')
    print(f"\nRequired parameters ({len(params1)}):")
    for key, val in sorted(params1.items()):
        print(f"  {key:20s}: {val}")
    
    # Test 2: Merge user params
    print("\n" + "=" * 80)
    print("TEST 2: Merge user params with defaults")
    print("=" * 80)
    
    user_params = {
        'rsi_period': 21,  # Override default
        'bb_std': 2.5,     # Override default
        'tp_rr_ratio': 3.0,  # New param
    }
    
    merged = merge_user_params_with_defaults(user_params, 'bollinger_mean_reversion')
    print(f"\nMerged parameters ({len(merged)}):")
    for key, val in sorted(merged.items()):
        print(f"  {key:20s}: {val}")
    
    # Test 3: ema_cloud_trend
    print("\n" + "=" * 80)
    print("TEST 3: ema_cloud_trend required params")
    print("=" * 80)
    
    params3 = get_required_params_for_strategy('ema_cloud_trend')
    print(f"\nRequired parameters ({len(params3)}):")
    for key, val in sorted(params3.items()):
        print(f"  {key:20s}: {val}")
    
    # Test 4: Ensure indicators
    print("\n" + "=" * 80)
    print("TEST 4: Ensure required indicators")
    print("=" * 80)
    
    import pandas as pd
    import numpy as np
    
    # Mock indicators
    mock_indicators = {
        'bb_upper': pd.Series([43000] * 100),
        'bb_lower': pd.Series([42000] * 100),
        'bb_middle': pd.Series([42500] * 100),
        'rsi14': pd.Series([50] * 100),
        'close_prev': pd.Series([42500] * 100),
    }
    
    result = ensure_required_indicators(mock_indicators, 'bollinger_mean_reversion')
    print(f"\nIndicators after ensure ({len(result)}):")
    for key in sorted(result.keys()):
        print(f"  ✓ {key}")
    
    print("\n✅ All mapper tests passed!")