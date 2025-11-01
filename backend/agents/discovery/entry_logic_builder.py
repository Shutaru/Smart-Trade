"""
Professional Entry Logic Builder - CRYPTO 24/7 OPTIMIZED

Converts indicator lists into robust trading rules using CROSSOVERS.
Uses crosses_above/crosses_below for momentum, static > < for filters.
Optimized for crypto (no session filters needed).
"""

from typing import Dict, List, Any


def build_professional_entry_logic(indicators: List[str], use_regime_filters: bool = True) -> Dict[str, Any]:
    """
    Build ROBUST entry logic using crossovers (more reliable than static thresholds)
    
    PHILOSOPHY:
    - entry_all: Trend FILTERS (ADX > 20, price > EMA200, REGIME) - use static comparisons
    - entry_any: Momentum TRIGGERS (RSI crosses above 30, MACD crossover) - use crossovers
    
    Args:
        indicators: List of indicator IDs from strategy catalog
        use_regime_filters: If True, add regime/macro filters to entry_all
    
    Returns:
        Dict with 'long' and 'short' entry conditions following this structure:
        {
            'long': {
                'entry_all': [...],  # ALL must be true (trend filters)
                'entry_any': [...]   # ANY can trigger (momentum signals)
            },
            'short': {...}
        }
    """
    
    # Mapping from strategy catalog IDs to backtest feature names
    # CRITICAL: Must match EXACTLY with backtest.py feat{} dict
    id_to_feat = {
        'ema_20': 'ema20',
        'ema_50': 'ema50',
        'ema_200': 'ema50',      # EMA200 não existe, usar ema50 como proxy
        'sma_20': 'ema20',
        'sma_50': 'ema50',
        'sma_200': 'ema50',
        'rsi_14': 'rsi14',
        'rsi_7': 'rsi5',
        'rsi_21': 'rsi14',
        'donchian': 'up55',
        'bollinger': 'bb_up',
        'atr': 'atr14',
        'adx': 'adx14',
        'cci': 'cci20',
        'stochastic': 'stoch_k',
        'mfi': 'mfi14',
        'macd': 'macd',
        'vwap': 'vwap',
        'obv': 'obv',
        'keltner': 'keltner_mid',
        'supertrend': 'supertrend'
    }
    
    long_all = []
    short_all = []
    long_any = []
    short_any = []
    
    # ============================================================================
    # TREND FOLLOWING STRATEGIES - Use CROSSOVERS + PULLBACKS
    # ============================================================================
    
    # EMA200 Trend Pullback: wait for pullback then re-enter
    if 'ema_200' in indicators and 'ema_50' in indicators and 'rsi_14' in indicators:
        # Long: close > ema_50, RSI pullback ≤ 40, re-enter on RSI > 50
        long_all.append({'indicator': 'close', 'op': '>', 'rhs_indicator': 'ema50'})
        long_any.append({'indicator': 'rsi14', 'op': 'crosses_above', 'rhs': 50.0})
        
        short_all.append({'indicator': 'close', 'op': '<', 'rhs_indicator': 'ema50'})
        short_any.append({'indicator': 'rsi14', 'op': 'crosses_below', 'rhs': 50.0})
    
    if 'supertrend' in indicators:
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'supertrend'})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'supertrend'})
    
    # MACD Zero Line Crossover (strong trend signal)
    if 'macd' in indicators and 'ema_200' in indicators:
        long_all.append({'indicator': 'close', 'op': '>', 'rhs_indicator': 'ema50'})
        long_any.append({'indicator': 'macd', 'op': 'crosses_above', 'rhs': 0.0})
        
        short_all.append({'indicator': 'close', 'op': '<', 'rhs_indicator': 'ema50'})
        short_any.append({'indicator': 'macd', 'op': 'crosses_below', 'rhs': 0.0})
    
    # EMA Stack (20 > 50 > 200)
    if 'ema_20' in indicators and 'ema_50' in indicators and 'ema_200' in indicators:
        long_all.append({'indicator': 'ema20', 'op': '>', 'rhs_indicator': 'ema50'})
        
        short_all.append({'indicator': 'ema20', 'op': '<', 'rhs_indicator': 'ema50'})
    
    # EMA20/EMA50 basic crossover
    if 'ema_20' in indicators and 'ema_50' in indicators and 'ema_200' not in indicators:
        long_any.append({'indicator': 'ema20', 'op': 'crosses_above', 'rhs_indicator': 'ema50'})
        short_any.append({'indicator': 'ema20', 'op': 'crosses_below', 'rhs_indicator': 'ema50'})
    
    if 'ema_20' in indicators and 'ema_50' not in indicators:
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'ema20'})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'ema20'})
    
    if 'ema_50' in indicators and 'ema_200' in indicators and 'ema_20' not in indicators:
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'ema50'})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'ema50'})
    
    if 'ema_200' in indicators and 'ema_50' not in indicators:
        long_all.append({'indicator': 'close', 'op': '>', 'rhs_indicator': 'ema50'})
        short_all.append({'indicator': 'close', 'op': '<', 'rhs_indicator': 'ema50'})
    
    if 'donchian' in indicators:
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'up55'})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'dn55'})
    
    # ============================================================================
    # MOMENTUM OSCILLATORS - Use CROSSOVERS + EXTREMES
    # ============================================================================
    
    # RSI + Bollinger Mean Reversion: touch BB-lower + RSI oversold
    if 'rsi_14' in indicators and 'bollinger' in indicators:
        # Long: touch/close below BB-lower + RSI ≤ 30 (oversold)
        long_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'bb_lo'})
        long_any.append({'indicator': 'rsi14', 'op': '<', 'rhs': 30.0})
        
        # Short: touch/close above BB-upper + RSI ≥ 70
        short_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'bb_up'})
        short_any.append({'indicator': 'rsi14', 'op': '>', 'rhs': 70.0})
    
    elif 'rsi_14' in indicators:
        # Standalone RSI: extreme crossovers only
        long_any.append({'indicator': 'rsi14', 'op': 'crosses_above', 'rhs': 25.0})
        short_any.append({'indicator': 'rsi14', 'op': 'crosses_below', 'rhs': 75.0})
    
    # Stochastic Fast Reversal: K crosses D in extreme zones
    if 'stochastic' in indicators:
        long_any.append({'indicator': 'stoch_k', 'op': 'crosses_above', 'rhs_indicator': 'stoch_d'})
        long_any.append({'indicator': 'stoch_k', 'op': '<', 'rhs': 30.0})
        
        short_any.append({'indicator': 'stoch_k', 'op': 'crosses_below', 'rhs_indicator': 'stoch_d'})
        short_any.append({'indicator': 'stoch_k', 'op': '>', 'rhs': 70.0})
    
    # CCI Extreme Snapback: CCI < -100 or > +100
    if 'cci' in indicators:
        long_any.append({'indicator': 'cci20', 'op': 'crosses_above', 'rhs': -100.0})
        short_any.append({'indicator': 'cci20', 'op': 'crosses_below', 'rhs': 100.0})
    
    # MFI Exhaustion: MFI ≤ 25 or ≥ 75 (volume-weighted extremes)
    if 'mfi' in indicators:
        long_any.append({'indicator': 'mfi14', 'op': 'crosses_above', 'rhs': 25.0})
        short_any.append({'indicator': 'mfi14', 'op': 'crosses_below', 'rhs': 75.0})
    
    if 'rsi_7' in indicators:
        long_any.append({'indicator': 'rsi5', 'op': 'crosses_above', 'rhs': 20.0})
        short_any.append({'indicator': 'rsi5', 'op': 'crosses_below', 'rhs': 80.0})
    
    # ============================================================================
    # VOLATILITY BREAKOUTS - Use CROSSOVERS + SQUEEZE DETECTION
    # ============================================================================
    
    # TTM Squeeze: BB inside KC (compression) → breakout when BB breaks KC
    if 'bollinger' in indicators and 'keltner' in indicators:
        # Squeeze release: BB_upper crosses above KC_upper (expansion!)
        long_any.append({'indicator': 'bb_up', 'op': 'crosses_above', 'rhs_indicator': 'keltner_up'})
        short_any.append({'indicator': 'bb_lo', 'op': 'crosses_below', 'rhs_indicator': 'keltner_lo'})
        # Also: price closes outside BB during squeeze
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'bb_up'})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'bb_lo'})
    
    elif 'bollinger' in indicators:
        # Bollinger mean reversion + breakout
        long_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'bb_lo'})
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'bb_mid'})
        short_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'bb_up'})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'bb_mid'})
    
    # Keltner Expansion: price closes outside KC
    if 'keltner' in indicators and 'bollinger' not in indicators:
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'keltner_up'})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'keltner_lo'})
    
    # ATR Filter: require volatility > 0
    if 'atr' in indicators:
        long_all.append({'indicator': 'atr14', 'op': '>', 'rhs': 0.0})
        short_all.append({'indicator': 'atr14', 'op': '>', 'rhs': 0.0})
    
    # ============================================================================
    # VOLUME INDICATORS - Follow Institutional Flow
    # ============================================================================
    
    # VWAP + MFI Trend Following: close > VWAP + MFI > 50 (buyers in control)
    if 'vwap' in indicators and 'mfi' in indicators:
        long_all.append({'indicator': 'close', 'op': '>', 'rhs_indicator': 'vwap'})
        long_all.append({'indicator': 'mfi14', 'op': '>', 'rhs': 50.0})
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'vwap'})
        
        short_all.append({'indicator': 'close', 'op': '<', 'rhs_indicator': 'vwap'})
        short_all.append({'indicator': 'mfi14', 'op': '<', 'rhs': 50.0})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'vwap'})
    
    elif 'vwap' in indicators:
        # VWAP standalone: reclaim/reject as trigger
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'vwap'})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'vwap'})
    
    # OBV Trend Confirm: OBV trending + SuperTrend alignment
    if 'obv' in indicators and 'supertrend' in indicators:
        long_all.append({'indicator': 'obv', 'op': '>', 'rhs': 0.0})
        long_any.append({'indicator': 'close', 'op': 'crosses_above', 'rhs_indicator': 'supertrend'})
        
        short_all.append({'indicator': 'obv', 'op': '<', 'rhs': 0.0})
        short_any.append({'indicator': 'close', 'op': 'crosses_below', 'rhs_indicator': 'supertrend'})
    
    elif 'obv' in indicators:
        # OBV simple: rising = bullish, falling = bearish
        long_any.append({'indicator': 'obv', 'op': '>', 'rhs': 0.0})
        short_any.append({'indicator': 'obv', 'op': '<', 'rhs': 0.0})
    
    # ============================================================================
    # TREND STRENGTH FILTERS - Static comparisons
    # ============================================================================
    
    if 'adx' in indicators:
        long_all.append({'indicator': 'adx14', 'op': '>', 'rhs': 20.0})
        short_all.append({'indicator': 'adx14', 'op': '>', 'rhs': 20.0})
        long_any.append({'indicator': 'adx14', 'op': 'crosses_above', 'rhs': 25.0})
        short_any.append({'indicator': 'adx14', 'op': 'crosses_above', 'rhs': 25.0})
    
    # ============================================================================
    # REGIME FILTERS (Automatic & Intelligent)
    # ============================================================================
    
    if use_regime_filters:
        # Classify strategy type based on indicators
        has_trend_strategy = any(ind in indicators for ind in [
            'supertrend', 'ema_20', 'ema_50', 'ema_200', 'macd', 'donchian', 'adx'
        ])
        has_mean_reversion = any(ind in indicators for ind in [
            'rsi_14', 'rsi_7', 'bollinger', 'stochastic', 'cci', 'mfi'
        ])
        has_breakout = any(ind in indicators for ind in [
            'keltner', 'atr', 'donchian'
        ]) and 'bollinger' in indicators
        
        # TREND FOLLOWING: Require strong trend (ADX ≥ 20)
        if has_trend_strategy and not has_mean_reversion:
            if 'adx' in indicators:
                # Ensure ADX filter is in entry_all
                if not any(c.get('indicator') == 'adx14' and c.get('op') == '>' for c in long_all):
                    long_all.append({'indicator': 'adx14', 'op': '>', 'rhs': 20.0})
                    short_all.append({'indicator': 'adx14', 'op': '>', 'rhs': 20.0})
        
        # MEAN REVERSION: Prefer ranging markets (ADX < 25)
        if has_mean_reversion and not has_trend_strategy:
            # Add implicit ADX < 25 filter (avoid strong trends)
            if not any(c.get('indicator') == 'adx14' for c in long_all):
                long_all.append({'indicator': 'adx14', 'op': '<', 'rhs': 25.0})
                short_all.append({'indicator': 'adx14', 'op': '<', 'rhs': 25.0})
        
        # BREAKOUT: Require low ADX → high ADX transition (squeeze → expansion)
        if has_breakout:
            # ADX rising from low levels (crosses above 20)
            if 'adx' in indicators:
                long_any.append({'indicator': 'adx14', 'op': 'crosses_above', 'rhs': 20.0})
                short_any.append({'indicator': 'adx14', 'op': 'crosses_above', 'rhs': 20.0})
    
    # ============================================================================
    # FALLBACK
    # ============================================================================
    
    if not long_any:
        long_any.append({'indicator': 'rsi14', 'op': 'crosses_above', 'rhs': 30.0})
    
    if not short_any:
        short_any.append({'indicator': 'rsi14', 'op': 'crosses_below', 'rhs': 70.0})
    
    return {
        'long': {'entry_all': long_all, 'entry_any': long_any},
        'short': {'entry_all': short_all, 'entry_any': short_any}
    }


if __name__ == '__main__':
    print("=" * 80)
    print("ENTRY LOGIC BUILDER - PROFESSIONAL STRATEGIES TEST")
    print("=" * 80)
    
    test_strategies = [
        {'name': 'ema200_trend_pullback', 'indicators': ['ema_200', 'ema_50', 'rsi_14', 'adx', 'atr']},
        {'name': 'ttm_squeeze_like', 'indicators': ['bollinger', 'keltner', 'adx', 'atr']},
        {'name': 'vwap_trend_with_mfi', 'indicators': ['vwap', 'mfi', 'adx', 'ema_50']},
        {'name': 'rsi_bollinger_revert', 'indicators': ['rsi_14', 'bollinger', 'ema_50']},
    ]
    
    for strategy in test_strategies:
        print(f"\n{'=' * 80}")
        print(f"Strategy: {strategy['name']}")
        print(f"Indicators: {', '.join(strategy['indicators'])}")
        print("=" * 80)
        
        logic = build_professional_entry_logic(strategy['indicators'])
        
        print("\nLONG CONDITIONS:")
        print(f"  entry_all (filters): {len(logic['long']['entry_all'])} conditions")
        for c in logic['long']['entry_all']:
            print(f"    - {c}")
        print(f"  entry_any (triggers): {len(logic['long']['entry_any'])} conditions")
        for c in logic['long']['entry_any']:
            print(f"    - {c}")
        
        print("\nSHORT CONDITIONS:")
        print(f"  entry_all (filters): {len(logic['short']['entry_all'])} conditions")
        print(f"  entry_any (triggers): {len(logic['short']['entry_any'])} conditions")