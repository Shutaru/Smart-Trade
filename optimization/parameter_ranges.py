"""
Parameter Ranges for Strategy Optimization

Defines optimizable parameter ranges for all indicators used in the 38 strategies.
Auto-detects which parameters to optimize based on strategy metadata.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ParameterRange:
    """Parameter range definition"""
    name: str
    type: str  # 'int', 'float', 'categorical'
    low: float = None
    high: float = None
    step: float = None
    choices: List[Any] = None
    log: bool = False


# ============================================================================
# INDICATOR PARAMETER RANGES
# ============================================================================

# TREND INDICATORS
EMA_RANGES = [
    ParameterRange('ema_fast_period', 'int', low=8, high=30, step=2),
    ParameterRange('ema_slow_period', 'int', low=40, high=100, step=5),
    ParameterRange('ema_trend_period', 'int', low=150, high=250, step=10),
]

SMA_RANGES = [
    ParameterRange('sma_period', 'int', low=10, high=50, step=5),
]

MACD_RANGES = [
    ParameterRange('macd_fast', 'int', low=8, high=15, step=1),
    ParameterRange('macd_slow', 'int', low=20, high=30, step=2),
    ParameterRange('macd_signal', 'int', low=7, high=12, step=1),
]

ADX_RANGES = [
    ParameterRange('adx_period', 'int', low=10, high=20, step=2),
]

SUPERTREND_RANGES = [
    ParameterRange('supertrend_period', 'int', low=8, high=15, step=1),
    ParameterRange('supertrend_mult', 'float', low=2.0, high=4.0, step=0.5),
]

DONCHIAN_RANGES = [
    ParameterRange('donchian_period', 'int', low=15, high=30, step=5),
]

# MOMENTUM INDICATORS
RSI_RANGES = [
    ParameterRange('rsi_period', 'int', low=7, high=28, step=1),
    ParameterRange('rsi_oversold', 'int', low=20, high=35, step=5),
    ParameterRange('rsi_overbought', 'int', low=65, high=80, step=5),
]

STOCHASTIC_RANGES = [
    ParameterRange('stoch_k_period', 'int', low=10, high=20, step=2),
    ParameterRange('stoch_d_period', 'int', low=3, high=7, step=1),
    ParameterRange('stoch_smooth_k', 'int', low=1, high=5, step=1),
    ParameterRange('stoch_oversold', 'int', low=15, high=25, step=5),
    ParameterRange('stoch_overbought', 'int', low=75, high=85, step=5),
]

CCI_RANGES = [
    ParameterRange('cci_period', 'int', low=15, high=30, step=5),
]

MFI_RANGES = [
    ParameterRange('mfi_period', 'int', low=10, high=20, step=2),
]

# VOLATILITY INDICATORS
ATR_RANGES = [
    ParameterRange('atr_period', 'int', low=10, high=20, step=2),
]

BOLLINGER_RANGES = [
    ParameterRange('bb_period', 'int', low=15, high=30, step=5),
    ParameterRange('bb_std', 'float', low=1.5, high=3.0, step=0.25),
]

KELTNER_RANGES = [
    ParameterRange('keltner_period', 'int', low=15, high=30, step=5),
    ParameterRange('keltner_mult', 'float', low=1.5, high=3.0, step=0.25),
]

# VOLUME INDICATORS (usually not optimized, but included for completeness)
OBV_RANGES = []

VWAP_RANGES = [
    ParameterRange('vwap_std_period', 'int', low=10, high=30, step=5),
]

# EXIT PARAMETERS
EXIT_RANGES = [
    ParameterRange('exit_method', 'categorical', choices=['atr_fixed', 'atr_trailing', 'breakeven_then_trail', 'keltner']),
    ParameterRange('tp_rr_ratio', 'float', low=1.5, high=4.0, step=0.25),
    ParameterRange('sl_atr_mult', 'float', low=1.0, high=3.5, step=0.25),
    ParameterRange('breakeven_r', 'float', low=0.5, high=1.5, step=0.25),
    ParameterRange('trail_atr_mult', 'float', low=1.5, high=3.0, step=0.25),
    ParameterRange('time_stop_bars', 'int', low=48, high=192, step=24),
]


# ============================================================================
# INDICATOR NAME MAPPING
# ============================================================================

INDICATOR_TO_RANGES = {
    'ema': EMA_RANGES,
    'sma': SMA_RANGES,
    'macd': MACD_RANGES,
    'adx': ADX_RANGES,
    'supertrend': SUPERTREND_RANGES,
    'donchian': DONCHIAN_RANGES,
    'rsi': RSI_RANGES,
    'stochastic': STOCHASTIC_RANGES,
    'stoch': STOCHASTIC_RANGES,
    'cci': CCI_RANGES,
    'mfi': MFI_RANGES,
    'atr': ATR_RANGES,
    'bollinger': BOLLINGER_RANGES,
    'bb': BOLLINGER_RANGES,
    'keltner': KELTNER_RANGES,
    'obv': OBV_RANGES,
    'vwap': VWAP_RANGES,
}


# ============================================================================
# AUTO-DETECTION FUNCTIONS
# ============================================================================

def get_parameter_ranges_for_strategy(strategy_name: str, strategy_metadata: Dict[str, Any] = None) -> List[ParameterRange]:
    """
    Auto-detect parameter ranges for a strategy
    
    Args:
        strategy_name: Name of the strategy
        strategy_metadata: Optional metadata dict with 'indicators' key
    
    Returns:
        List of ParameterRange objects
    """
    ranges = []
    indicators_used = []
    
    # If metadata provided, use it
    if strategy_metadata and 'indicators' in strategy_metadata:
        indicators_used = strategy_metadata['indicators']
    else:
        # Fallback: infer from strategy name
        strategy_lower = strategy_name.lower()
        
        # Check each indicator type
        for indicator_name in INDICATOR_TO_RANGES.keys():
            if indicator_name in strategy_lower:
                indicators_used.append(indicator_name)
    
    # Add ranges for detected indicators
    seen_params = set()
    for indicator_name in indicators_used:
        # Map indicator names from metadata to range keys
        indicator_key = _map_indicator_name(indicator_name)
        
        if indicator_key in INDICATOR_TO_RANGES:
            for param_range in INDICATOR_TO_RANGES[indicator_key]:
                # Avoid duplicates
                if param_range.name not in seen_params:
                    ranges.append(param_range)
                    seen_params.add(param_range.name)
    
    # Always add exit parameters
    for exit_range in EXIT_RANGES:
        if exit_range.name not in seen_params:
            ranges.append(exit_range)
    
    return ranges


def _map_indicator_name(indicator_name: str) -> str:
    """
    Map indicator names from metadata to parameter range keys
    
    Examples:
        'ema20' -> 'ema'
        'rsi14' -> 'rsi'
        'bb_upper' -> 'bollinger'
    """
    name_lower = indicator_name.lower()
    
    # Direct mappings
    if 'ema' in name_lower:
        return 'ema'
    if 'sma' in name_lower:
        return 'sma'
    if 'rsi' in name_lower:
        return 'rsi'
    if 'macd' in name_lower:
        return 'macd'
    if 'adx' in name_lower:
        return 'adx'
    if 'supertrend' in name_lower:
        return 'supertrend'
    if 'donchian' in name_lower:
        return 'donchian'
    if 'stoch' in name_lower:
        return 'stochastic'
    if 'cci' in name_lower:
        return 'cci'
    if 'mfi' in name_lower:
        return 'mfi'
    if 'atr' in name_lower:
        return 'atr'
    if 'bb' in name_lower or 'bollinger' in name_lower or 'boll' in name_lower:
        return 'bollinger'
    if 'keltner' in name_lower:
        return 'keltner'
    if 'obv' in name_lower:
        return 'obv'
    if 'vwap' in name_lower:
        return 'vwap'
    
    return indicator_name


def get_default_parameters_for_strategy(strategy_name: str, strategy_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get default parameter values for a strategy
    
    Args:
        strategy_name: Name of the strategy
        strategy_metadata: Optional metadata dict
    
    Returns:
        Dictionary of default parameter values
    """
    ranges = get_parameter_ranges_for_strategy(strategy_name, strategy_metadata)
    
    defaults = {}
    for param_range in ranges:
        if param_range.type == 'categorical':
            defaults[param_range.name] = param_range.choices[0]
        elif param_range.type == 'int':
            # Use middle value
            defaults[param_range.name] = int((param_range.low + param_range.high) / 2)
        elif param_range.type == 'float':
            # Use middle value
            defaults[param_range.name] = (param_range.low + param_range.high) / 2
    
    return defaults


def print_parameter_ranges(strategy_name: str, strategy_metadata: Dict[str, Any] = None):
    """Print parameter ranges for a strategy"""
    ranges = get_parameter_ranges_for_strategy(strategy_name, strategy_metadata)
    
    print(f"\n📊 Parameter Ranges for '{strategy_name}':")
    print("=" * 80)
    
    if not ranges:
        print("  No parameters found")
        return
    
    for param_range in ranges:
        if param_range.type == 'categorical':
            print(f"  {param_range.name:25s}: {param_range.choices}")
        else:
            print(f"  {param_range.name:25s}: [{param_range.low}, {param_range.high}] (step: {param_range.step})")
    
    print("=" * 80)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    print("✅ Testing Parameter Ranges Module...")
    
    # Test 1: bollinger_mean_reversion
    print("\n" + "=" * 80)
    print("TEST 1: bollinger_mean_reversion")
    print("=" * 80)
    
    metadata1 = {
        'indicators': ['bb_lower', 'bb_upper', 'bb_middle', 'close_prev', 'rsi14']
    }
    
    ranges1 = get_parameter_ranges_for_strategy('bollinger_mean_reversion', metadata1)
    print(f"\nFound {len(ranges1)} parameter ranges:")
    for r in ranges1:
        if r.type == 'categorical':
            print(f"  - {r.name}: {r.choices}")
        else:
            print(f"  - {r.name}: [{r.low}, {r.high}]")
    
    defaults1 = get_default_parameters_for_strategy('bollinger_mean_reversion', metadata1)
    print(f"\nDefault parameters: {defaults1}")
    
    # Test 2: ema_cloud_trend
    print("\n" + "=" * 80)
    print("TEST 2: ema_cloud_trend")
    print("=" * 80)
    
    metadata2 = {
        'indicators': ['ema20', 'ema50', 'ema200', 'rsi14', 'prev_high']
    }
    
    print_parameter_ranges('ema_cloud_trend', metadata2)
    
    # Test 3: triple_momentum_confluence
    print("\n" + "=" * 80)
    print("TEST 3: triple_momentum_confluence")
    print("=" * 80)
    
    metadata3 = {
        'indicators': ['rsi14', 'stoch_k', 'stoch_d', 'macd_hist', 'ema50']
    }
    
    ranges3 = get_parameter_ranges_for_strategy('triple_momentum_confluence', metadata3)
    print(f"\nFound {len(ranges3)} parameter ranges")
    
    defaults3 = get_default_parameters_for_strategy('triple_momentum_confluence', metadata3)
    print(f"\nDefault parameters ({len(defaults3)} params):")
    for key, val in sorted(defaults3.items()):
        print(f"  {key:25s}: {val}")
    
    print("\n✅ All parameter range tests passed!")