"""
Strategy Catalog - All Available Indicators

Defines all indicators and their combinations for strategy discovery.
LLM will select optimal combinations based on market regime.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


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
    def generate_combinations(max_indicators: int = 3) -> List[Dict[str, Any]]:
        """
        Generate intelligent indicator combinations
        
        Rules:
        - Always include 1 trend indicator
        - Always include 1 momentum indicator
        - Optionally add volatility or volume
        """
        catalog = StrategyCatalog()
        
        trend_indicators = list(catalog.get_by_type('trend').keys())
        momentum_indicators = list(catalog.get_by_type('momentum').keys())
        volatility_indicators = list(catalog.get_by_type('volatility').keys())
        volume_indicators = list(catalog.get_by_type('volume').keys())
        
        combinations = []
        
        # Strategy 1: Trend + Momentum
        for trend in ['ema_20', 'ema_50', 'macd', 'supertrend']:
            for momentum in ['rsi_14', 'stochastic', 'cci']:
                combinations.append({
                    'name': f'{trend}_{momentum}',
                    'indicators': [trend, momentum],
                    'entry_logic': 'trend_aligned AND momentum_oversold',
                    'exit_logic': 'momentum_overbought OR trend_reversal'
                })
        
        # Strategy 2: Trend + Momentum + Volatility
        for trend in ['ema_20', 'supertrend']:
            for momentum in ['rsi_14', 'mfi']:
                for vol in ['bollinger', 'atr']:
                    combinations.append({
                        'name': f'{trend}_{momentum}_{vol}',
                        'indicators': [trend, momentum, vol],
                        'entry_logic': 'trend_aligned AND momentum_oversold AND low_volatility',
                        'exit_logic': 'high_volatility OR momentum_overbought'
                    })
        
        # Strategy 3: Multi-timeframe
        combinations.append({
            'name': 'multi_tf_ema_rsi',
            'indicators': ['ema_20', 'ema_50', 'ema_200', 'rsi_14'],
            'entry_logic': 'ema_20 > ema_50 > ema_200 AND rsi < 40',
            'exit_logic': 'rsi > 70 OR ema_20 < ema_50'
        })
        
        # Strategy 4: Mean reversion
        combinations.append({
            'name': 'mean_reversion_bb_rsi',
            'indicators': ['bollinger', 'rsi_14', 'mfi'],
            'entry_logic': 'price < bb_lower AND rsi < 30 AND mfi < 20',
            'exit_logic': 'price > bb_middle OR rsi > 50'
        })
        
        # Strategy 5: Breakout
        combinations.append({
            'name': 'breakout_donchian_adx',
            'indicators': ['donchian', 'adx', 'atr'],
            'entry_logic': 'price > donchian_upper AND adx > 25 AND atr_rising',
            'exit_logic': 'price < donchian_middle OR adx < 20'
        })
        
        return combinations[:20]  # Limit to 20 strategies


if __name__ == '__main__':
    # Test catalog
    catalog = StrategyCatalog()
    
    print("📊 Available Indicators:")
    print(f"Total: {len(catalog.INDICATORS)}")
    print(f"\nBy type: {catalog.get_summary()}")

    print("\n🎯 Strategy Templates:")
    templates = StrategyTemplate.generate_combinations()
    for i, template in enumerate(templates[:5], 1):
        print(f"\n{i}. {template['name']}")
        print(f"   Indicators: {', '.join(template['indicators'])}")
        print(f"   Entry: {template['entry_logic']}")