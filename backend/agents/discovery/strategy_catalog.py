"""
Strategy Catalog - All Available Indicators

Defines all indicators and their combinations for strategy discovery.
LLM will select optimal combinations based on market regime.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import random


@dataclass
class Indicator:
    """Indicator definition"""
    id: str
    name: str
    type: str  # 'trend', 'momentum', 'volatility', 'volume'
    params: Dict[str, Any]
    output_fields: List[str]
    description: str


class StrategyCatalog:
    """
    Catalog of all available indicators for strategy discovery
    
    Categories:
    - Trend: EMA, SMA, MACD, ADX, SuperTrend, Donchian
    - Momentum: RSI, Stochastic, CCI, MFI
    - Volatility: ATR, Bollinger Bands, Keltner Channels
    - Volume: OBV, VWAP
    """
    
    INDICATORS = {
        # ============================================================================
        # TREND INDICATORS
        # ============================================================================
        
        'ema_20': Indicator(
            id='ema_20',
            name='EMA 20',
            type='trend',
            params={'period': 20},
            output_fields=['ema'],
            description='Fast exponential moving average'
        ),
        
        'ema_50': Indicator(
            id='ema_50',
            name='EMA 50',
            type='trend',
            params={'period': 50},
            output_fields=['ema'],
            description='Medium exponential moving average'
        ),
        
        'ema_200': Indicator(
            id='ema_200',
            name='EMA 200',
            type='trend',
            params={'period': 200},
            output_fields=['ema'],
            description='Slow exponential moving average'
        ),
        
        'sma_20': Indicator(
            id='sma_20',
            name='SMA 20',
            type='trend',
            params={'period': 20},
            output_fields=['sma'],
            description='Simple moving average 20'
        ),
        
        'sma_50': Indicator(
            id='sma_50',
            name='SMA 50',
            type='trend',
            params={'period': 50},
            output_fields=['sma'],
            description='Simple moving average 50'
        ),
        
        'sma_200': Indicator(
            id='sma_200',
            name='SMA 200',
            type='trend',
            params={'period': 200},
            output_fields=['sma'],
            description='Simple moving average 200'
        ),
        
        'macd': Indicator(
            id='macd',
            name='MACD',
            type='trend',
            params={'fast': 12, 'slow': 26, 'signal': 9},
            output_fields=['macd', 'signal', 'histogram'],
            description='Moving Average Convergence Divergence'
        ),
        
        'adx': Indicator(
            id='adx',
            name='ADX',
            type='trend',
            params={'period': 14},
            output_fields=['adx', 'plus_di', 'minus_di'],
            description='Average Directional Index (trend strength)'
        ),
        
        'supertrend': Indicator(
            id='supertrend',
            name='SuperTrend',
            type='trend',
            params={'period': 10, 'multiplier': 3.0},
            output_fields=['supertrend', 'direction'],
            description='Volatility-based trend indicator'
        ),
        
        'donchian': Indicator(
            id='donchian',
            name='Donchian Channels',
            type='trend',
            params={'period': 20},
            output_fields=['donchian_upper', 'donchian_lower', 'donchian_middle'],
            description='Breakout channels based on high/low'
        ),
        
        # ============================================================================
        # MOMENTUM INDICATORS
        # ============================================================================
        
        'rsi_14': Indicator(
            id='rsi_14',
            name='RSI 14',
            type='momentum',
            params={'period': 14},
            output_fields=['rsi'],
            description='Relative Strength Index (standard)'
        ),
        
        'rsi_7': Indicator(
            id='rsi_7',
            name='RSI 7',
            type='momentum',
            params={'period': 7},
            output_fields=['rsi'],
            description='Fast RSI for scalping'
        ),
        
        'rsi_21': Indicator(
            id='rsi_21',
            name='RSI 21',
            type='momentum',
            params={'period': 21},
            output_fields=['rsi'],
            description='Slow RSI for swing trading'
        ),
        
        'stochastic': Indicator(
            id='stochastic',
            name='Stochastic Oscillator',
            type='momentum',
            params={'k_period': 14, 'd_period': 3},
            output_fields=['stoch_k', 'stoch_d'],
            description='Momentum oscillator (0-100)'
        ),
        
        'cci': Indicator(
            id='cci',
            name='CCI',
            type='momentum',
            params={'period': 20},
            output_fields=['cci'],
            description='Commodity Channel Index'
        ),
        
        'mfi': Indicator(
            id='mfi',
            name='MFI',
            type='momentum',
            params={'period': 14},
            output_fields=['mfi'],
            description='Money Flow Index (volume-weighted RSI)'
        ),
        
        # ============================================================================
        # VOLATILITY INDICATORS
        # ============================================================================
        
        'atr': Indicator(
            id='atr',
            name='ATR',
            type='volatility',
            params={'period': 14},
            output_fields=['atr'],
            description='Average True Range (volatility)'
        ),
        
        'bollinger': Indicator(
            id='bollinger',
            name='Bollinger Bands',
            type='volatility',
            params={'period': 20, 'std': 2.0},
            output_fields=['bb_upper', 'bb_middle', 'bb_lower'],
            description='Volatility bands (mean ± 2σ)'
        ),
        
        'keltner': Indicator(
            id='keltner',
            name='Keltner Channels',
            type='volatility',
            params={'period': 20, 'multiplier': 2.0},
            output_fields=['keltner_upper', 'keltner_middle', 'keltner_lower'],
            description='ATR-based volatility channels'
        ),
        
        # ============================================================================
        # VOLUME INDICATORS
        # ============================================================================
        
        'obv': Indicator(
            id='obv',
            name='OBV',
            type='volume',
            params={},
            output_fields=['obv'],
            description='On-Balance Volume (cumulative volume flow)'
        ),
        
        'vwap': Indicator(
            id='vwap',
            name='VWAP',
            type='volume',
            params={},
            output_fields=['vwap'],
            description='Volume Weighted Average Price'
        ),
    }
    
    @classmethod
    def get_all_indicators(cls) -> Dict[str, Indicator]:
        """Get all available indicators"""
        return cls.INDICATORS
    
    @classmethod
    def get_by_type(cls, indicator_type: str) -> Dict[str, Indicator]:
        """Get indicators by type (trend, momentum, volatility, volume)"""
        return {
            id: ind 
            for id, ind in cls.INDICATORS.items() 
            if ind.type == indicator_type
        }
    
    @classmethod
    def get_indicator(cls, indicator_id: str) -> Indicator:
        """Get specific indicator by ID"""
        return cls.INDICATORS.get(indicator_id)
    
    @classmethod
    def list_ids(cls) -> List[str]:
        """List all indicator IDs"""
        return list(cls.INDICATORS.keys())
    
    @classmethod
    def get_summary(cls) -> Dict[str, int]:
        """Get summary of available indicators by type"""
        summary = {}
        for ind in cls.INDICATORS.values():
            summary[ind.type] = summary.get(ind.type, 0) + 1
        return summary


# ============================================================================
# STRATEGY TEMPLATES
# ============================================================================

class StrategyTemplate:
    """
    Template for strategy definition
    
    A strategy combines:
    - Entry indicators (e.g., RSI < 30 AND MACD > 0)
    - Exit indicators (e.g., RSI > 70 OR ATR > 2x)
    - Risk management (stop-loss, take-profit)
    """
    
    @staticmethod
    def generate_combinations(max_indicators: int = 5) -> List[Dict[str, Any]]:
        """
        Generate 38 professional strategy archetypes (cycle-agnostic, battle-tested)
        
        Categories:
        A) Trend Following (6): Ride sustained moves with pullback entries
        B) Mean Reversion (6): Fade extremes in ranging markets
        C) Breakout / Vol Expansion (6): Capture volatility expansions
        D) Volume / Flow (5): Follow institutional money flow
        E) Hybrid / Multi-factor (5): Combine multiple confirmations
        F) Session / Context (6): Time-based + intraday edge
        G) Price Action + Filters (4): Pure structure with minimal indicators
        
        Conventions:
        - Regime filters: close > ema_200 (bull), adx ≥ 20-25 (trend), adx < 20 (range)
        - Exits: SL = 1.5-2.5×ATR, TP = 2-3R, Trail = 1.5-3.0×ATR
        - Parameters: RSI_OS=20-40, RSI_OB=60-80, ADX_TREND=18-30
        """
        
        combinations = []
        
        # ============================================================================
        # A) TREND FOLLOWING (6)
        # ============================================================================
        combinations.extend([
            {'name': 'ema200_trend_pullback', 'indicators': ['ema_200', 'ema_50', 'rsi_14', 'adx', 'atr']},
            {'name': 'supertrend_continuation', 'indicators': ['supertrend', 'adx', 'atr', 'rsi_14']},
            {'name': 'macd_zero_line_trend', 'indicators': ['macd', 'ema_200', 'adx', 'atr']},
            {'name': 'donchian_trend_ride', 'indicators': ['donchian', 'adx', 'atr', 'rsi_14']},
            {'name': 'adx_filtered_ema_stack', 'indicators': ['ema_20', 'ema_50', 'ema_200', 'adx', 'atr']},
            {'name': 'vwap_trend_follow', 'indicators': ['vwap', 'ema_50', 'adx', 'atr']},
        ])
        
        # ============================================================================
        # B) MEAN REVERSION (6)
        # ============================================================================
        combinations.extend([
            {'name': 'rsi_bollinger_revert', 'indicators': ['rsi_14', 'bollinger', 'ema_50']},
            {'name': 'stoch_fast_reversal', 'indicators': ['stochastic', 'ema_50', 'atr']},
            {'name': 'cci_extreme_snapback', 'indicators': ['cci', 'bollinger', 'atr']},
            {'name': 'mfi_exhaustion_vwap', 'indicators': ['mfi', 'vwap', 'rsi_14']},
            {'name': 'obv_range_fade', 'indicators': ['obv', 'bollinger', 'ema_50']},
            {'name': 'vwap_std_revert', 'indicators': ['vwap', 'bollinger', 'atr']},
        ])
        
        # ============================================================================
        # C) BREAKOUT / VOL EXPANSION (6)
        # ============================================================================
        combinations.extend([
            {'name': 'ttm_squeeze_like', 'indicators': ['bollinger', 'keltner', 'adx', 'atr']},
            {'name': 'donchian_breakout_atr', 'indicators': ['donchian', 'atr', 'adx', 'rsi_14']},
            {'name': 'keltner_expansion_macd', 'indicators': ['keltner', 'macd', 'atr', 'rsi_14']},
            {'name': 'atr_surge_adx_rise', 'indicators': ['atr', 'adx', 'ema_50']},
            {'name': 'channel_break_and_go', 'indicators': ['bollinger', 'keltner', 'adx']},
            {'name': 'retest_break_go', 'indicators': ['donchian', 'ema_20', 'atr']},
        ])
        
        # ============================================================================
        # D) VOLUME / FLOW (5)
        # ============================================================================
        combinations.extend([
            {'name': 'vwap_trend_with_mfi', 'indicators': ['vwap', 'mfi', 'adx', 'ema_50']},
            {'name': 'obv_trend_confirm', 'indicators': ['obv', 'supertrend', 'adx']},
            {'name': 'mfi_div_regime_filter', 'indicators': ['mfi', 'rsi_14', 'ema_200']},
            {'name': 'vwap_reclaim_breakout', 'indicators': ['vwap', 'donchian', 'atr']},
            {'name': 'obv_slope_break', 'indicators': ['obv', 'keltner', 'adx']},
        ])
        
        # ============================================================================
        # E) HYBRID / MULTI-FACTOR (5)
        # ============================================================================
        combinations.extend([
            {'name': 'triple_momentum_stack', 'indicators': ['rsi_14', 'stochastic', 'macd', 'ema_50']},
            {'name': 'supertrend_vwap_adx', 'indicators': ['supertrend', 'vwap', 'adx', 'atr']},
            {'name': 'ema_cross_squeeze', 'indicators': ['ema_20', 'ema_50', 'bollinger', 'adx']},
            {'name': 'regime_adaptive_dual', 'indicators': ['ema_200', 'adx', 'rsi_14', 'atr']},
            {'name': 'complete_system_pro', 'indicators': ['supertrend', 'rsi_14', 'atr', 'vwap', 'adx']},
        ])
        
        # ============================================================================
        # F) SESSION / CONTEXT (6) - Crypto 24/7 adapted
        # ============================================================================
        combinations.extend([
            {'name': 'london_breakout_atr', 'indicators': ['donchian', 'atr', 'ema_50', 'adx']},
            {'name': 'ny_open_momentum', 'indicators': ['vwap', 'atr', 'rsi_14', 'adx']},
            {'name': 'ny_session_fade', 'indicators': ['rsi_14', 'bollinger', 'atr', 'ema_20']},
            {'name': 'weekend_mean_revert', 'indicators': ['vwap', 'bollinger', 'rsi_14']},
            {'name': 'trend_day_continuation', 'indicators': ['adx', 'supertrend', 'ema_20']},
            {'name': 'donchian_break_retest_intraday', 'indicators': ['donchian', 'ema_20', 'vwap']},
        ])
        
        # ============================================================================
        # G) PRICE ACTION + FILTERS (4)
        # ============================================================================
        combinations.extend([
            {'name': 'pure_price_action_plus', 'indicators': ['donchian', 'ema_200', 'atr']},
            {'name': 'failed_breakout_reversal', 'indicators': ['bollinger', 'vwap', 'rsi_14']},
            {'name': 'two_leg_pullback_trend', 'indicators': ['ema_50', 'adx', 'rsi_14']},
            {'name': 'opening_range_breakout_v2', 'indicators': ['donchian', 'atr', 'adx']},
        ])
        
        return combinations


if __name__ == '__main__':
    # Test catalog
    catalog = StrategyCatalog()
    
    print("📊 Available Indicators:")
    print(f"Total: {len(catalog.INDICATORS)}")
    print(f"\nBy type: {catalog.get_summary()}")
    
    print("\n🎯 Strategy Templates:")
    templates = StrategyTemplate.generate_combinations()
    print(f"Total strategies: {len(templates)}\n")
    
    for i, template in enumerate(templates, 1):
        print(f"{i}. {template['name']}")
        print(f"   Indicators: {', '.join(template['indicators'])}")