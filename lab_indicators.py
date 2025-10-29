"""Indicator catalog for Strategy Lab with smart operator recommendations"""

# Indicator categories
CATEGORY_OSCILLATOR = "oscillator"  # RSI, Stochastic, Williams %R (bounded 0-100)
CATEGORY_TREND = "trend"  # EMA, SMA, SuperTrend (price-following)
CATEGORY_MOMENTUM = "momentum"  # MACD, ROC (unbounded momentum)
CATEGORY_VOLATILITY = "volatility"  # ATR, Bollinger Bands
CATEGORY_VOLUME = "volume"  # OBV, MFI
CATEGORY_STRENGTH = "strength"  # ADX (trend strength)

INDICATOR_CATALOG = [
    {
      "id": "rsi",
        "name": "RSI (Relative Strength Index)",
        "category": CATEGORY_OSCILLATOR,
   "range": {"min": 0, "max": 100, "bounded": True},
        "params": {
          "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
     "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum oscillator measuring speed and change of price movements",
        "recommended_operators": [
    "crosses_above",  # RSI crosses above 30 (oversold → bullish)
            "crosses_below",# RSI crosses below 70 (overbought → bearish)
      ">",  # RSI > 50 (bullish momentum)
            "<",  # RSI < 30 (oversold)
   "between"  # RSI between 40-60 (neutral zone)
    ],
        "typical_levels": {
  "oversold": 30,
   "neutral": 50,
        "overbought": 70,
 "extreme_oversold": 20,
    "extreme_overbought": 80
        },
        "usage_hint": "Use crossover/crossunder for entry signals, > or < for filters"
    },
    {
        "id": "williams_r",
   "name": "Williams %R",
        "category": CATEGORY_OSCILLATOR,
        "range": {"min": -100, "max": 0, "bounded": True},
        "params": {
            "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum indicator measuring overbought/oversold",
        "recommended_operators": [
          "crosses_above",  # Williams %R crosses above -80 (oversold → bullish)
            "crosses_below",  # Williams %R crosses below -20 (overbought → bearish)
            ">",  # Williams %R > -50 (bullish)
   "<"   # Williams %R < -80 (oversold)
      ],
        "typical_levels": {
         "oversold": -80,
            "neutral": -50,
            "overbought": -20,
            "extreme_oversold": -90,
      "extreme_overbought": -10
        },
    "usage_hint": "Inverted scale: -80 to -100 is oversold, -20 to 0 is overbought"
    },
    {
 "id": "stoch",
     "name": "Stochastic Oscillator",
     "category": CATEGORY_OSCILLATOR,
   "range": {"min": 0, "max": 100, "bounded": True},
 "params": {
            "k_period": {"type": "int", "default": 14, "min": 2, "max": 100},
          "d_period": {"type": "int", "default": 3, "min": 2, "max": 50},
  "smooth_k": {"type": "int", "default": 3, "min": 1, "max": 10}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum indicator comparing closing price to price range",
        "recommended_operators": [
            "crosses_above",  # %K crosses above %D (bullish crossover)
         "crosses_below",  # %K crosses below %D (bearish crossover)
            ">",  # Stoch > 80 (overbought)
          "<"   # Stoch < 20 (oversold)
      ],
        "typical_levels": {
            "oversold": 20,
      "neutral": 50,
            "overbought": 80
        },
        "usage_hint": "Best for crossover signals: %K crosses %D in oversold/overbought zones"
    },
    {
        "id": "ema",
        "name": "EMA (Exponential Moving Average)",
  "category": CATEGORY_TREND,
        "range": {"bounded": False},
        "params": {
  "period": {"type": "int", "default": 20, "min": 2, "max": 500}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
    "description": "Moving average giving more weight to recent prices",
        "recommended_operators": [
       "crosses_above",  # Price crosses above EMA (bullish breakout)
         "crosses_below",  # Price crosses below EMA (bearish breakdown)
   ">",  # Price > EMA (uptrend)
       "<"   # Price < EMA (downtrend)
        ],
        "usage_hint": "Compare with price or other EMAs. Use crossovers for trend changes"
    },
    {
        "id": "sma",
      "name": "SMA (Simple Moving Average)",
        "category": CATEGORY_TREND,
        "range": {"bounded": False},
        "params": {
      "period": {"type": "int", "default": 20, "min": 2, "max": 500}
  },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
     "description": "Arithmetic mean of prices",
        "recommended_operators": [
  "crosses_above",  # Price crosses above SMA
     "crosses_below",  # Price crosses below SMA
            ">",  # Price > SMA (above average)
  "<"   # Price < SMA (below average)
        ],
        "usage_hint": "Golden cross: SMA(50) crosses above SMA(200)"
    },
    {
        "id": "supertrend",
        "name": "Supertrend",
        "category": CATEGORY_TREND,
   "range": {"bounded": False},
        "params": {
       "period": {"type": "int", "default": 10, "min": 2, "max": 50},
  "multiplier": {"type": "float", "default": 3.0, "min": 1.0, "max": 10.0}
     },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Trend-following indicator based on ATR",
        "recommended_operators": [
    "crosses_above",  # Price crosses above SuperTrend (trend reversal to bullish)
            "crosses_below",  # Price crosses below SuperTrend (trend reversal to bearish)
 ">",  # Price > SuperTrend (uptrend confirmed)
  "<"   # Price < SuperTrend (downtrend confirmed)
        ],
    "usage_hint": "Best for trend following: enter when price crosses SuperTrend line"
    },
    {
        "id": "macd",
        "name": "MACD (Moving Average Convergence Divergence)",
        "category": CATEGORY_MOMENTUM,
"range": {"bounded": False},
        "params": {
            "fast": {"type": "int", "default": 12, "min": 2, "max": 50},
            "slow": {"type": "int", "default": 26, "min": 2, "max": 100},
"signal": {"type": "int", "default": 9, "min": 2, "max": 50}
        },
    "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
   "description": "Trend-following momentum indicator",
        "recommended_operators": [
         "crosses_above",  # MACD crosses above signal (bullish crossover)
            "crosses_below",  # MACD crosses below signal (bearish crossover)
 ">",  # MACD > 0 (positive momentum)
      "<" # MACD < 0 (negative momentum)
        ],
        "typical_levels": {
       "zero_line": 0
        },
        "usage_hint": "Best for crossover signals and divergence detection"
    },
    {
        "id": "atr",
     "name": "ATR (Average True Range)",
        "category": CATEGORY_VOLATILITY,
        "range": {"bounded": False, "min": 0},
        "params": {
            "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
   "description": "Volatility indicator",
     "recommended_operators": [
    ">",  # ATR > threshold (high volatility)
            "<",  # ATR < threshold (low volatility)
 "crosses_above"  # ATR expanding (volatility breakout)
        ],
   "usage_hint": "Use for position sizing and stop-loss placement, not entries"
    },
    {
        "id": "adx",
      "name": "ADX (Average Directional Index)",
        "category": CATEGORY_STRENGTH,
        "range": {"min": 0, "max": 100, "bounded": True},
  "params": {
            "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
     "description": "Trend strength indicator",
 "recommended_operators": [
            ">",# ADX > 25 (strong trend)
  "<",  # ADX < 20 (weak trend / ranging)
            "crosses_above"  # ADX crosses above 25 (trend strengthening)
      ],
     "typical_levels": {
            "weak_trend": 20,
       "strong_trend": 25,
            "very_strong_trend": 40
        },
        "usage_hint": "Filter: only trade when ADX > 25 for trend strategies"
    },
    {
  "id": "cci",
        "name": "CCI (Commodity Channel Index)",
        "category": CATEGORY_OSCILLATOR,
    "range": {"bounded": False},  # Typically -200 to +200 but unbounded
        "params": {
            "period": {"type": "int", "default": 20, "min": 2, "max": 100}
        },
      "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum oscillator",
        "recommended_operators": [
   "crosses_above",  # CCI crosses above -100 (oversold → bullish)
      "crosses_below",  # CCI crosses below +100 (overbought → bearish)
            ">",  # CCI > 0 (bullish)
   "<",  # CCI < -100 (oversold)
      "between"  # CCI between -100 and +100 (normal range)
        ],
        "typical_levels": {
    "oversold": -100,
            "neutral": 0,
  "overbought": 100
        },
    "usage_hint": "Mean reversion: buy when CCI < -100, sell when CCI > +100"
    },
    {
      "id": "bollinger",
   "name": "Bollinger Bands",
        "category": CATEGORY_VOLATILITY,
  "range": {"bounded": False},
        "params": {
  "period": {"type": "int", "default": 20, "min": 2, "max": 100},
    "std_dev": {"type": "float", "default": 2.0, "min": 0.5, "max": 5.0}
        },
 "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Volatility bands",
    "recommended_operators": [
            "crosses_above",  # Price crosses above upper band (breakout)
      "crosses_below",  # Price crosses below lower band (oversold)
            ">",  # Price > upper band (overbought)
   "<"   # Price < lower band (oversold)
        ],
   "usage_hint": "Mean reversion: buy at lower band, sell at upper band"
    },
    {
        "id": "keltner",
        "name": "Keltner Channels",
        "category": CATEGORY_VOLATILITY,
        "range": {"bounded": False},
        "params": {
     "period": {"type": "int", "default": 20, "min": 2, "max": 100},
 "atr_mult": {"type": "float", "default": 2.0, "min": 0.5, "max": 5.0}
     },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
     "description": "Volatility-based envelopes",
  "recommended_operators": [
   "crosses_above",  # Price crosses above upper channel
"crosses_below",  # Price crosses below lower channel
    ">",  # Price > upper channel (breakout)
            "<" # Price < lower channel (breakdown)
        ],
      "usage_hint": "Similar to Bollinger Bands but uses ATR instead of standard deviation"
    },
  {
   "id": "donchian",
        "name": "Donchian Channels",
      "category": CATEGORY_VOLATILITY,
 "range": {"bounded": False},
    "params": {
    "period": {"type": "int", "default": 20, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
    "description": "Channel formed by highest high and lowest low",
        "recommended_operators": [
            "crosses_above",  # Price crosses above upper channel (breakout)
      "crosses_below",  # Price crosses below lower channel (breakdown)
   "==",  # Price touches upper/lower channel
   ],
     "usage_hint": "Breakout strategy: enter when price breaks upper/lower channel"
    },
    {
        "id": "vwap",
 "name": "VWAP (Volume Weighted Average Price)",
      "category": CATEGORY_VOLUME,
 "range": {"bounded": False},
        "params": {},
   "supported_timeframes": ["5m", "15m", "1h"],
        "description": "Average price weighted by volume",
   "recommended_operators": [
 "crosses_above",  # Price crosses above VWAP (bullish)
    "crosses_below",  # Price crosses below VWAP (bearish)
            ">",  # Price > VWAP (institutional buying)
   "<"   # Price < VWAP (institutional selling)
   ],
        "usage_hint": "Institutional benchmark: trade above VWAP is bullish"
    },
    {
     "id": "obv",
 "name": "OBV (On Balance Volume)",
    "category": CATEGORY_VOLUME,
        "range": {"bounded": False},
        "params": {},
   "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
    "description": "Momentum indicator relating volume to price",
   "recommended_operators": [
      "crosses_above",  # OBV crosses above moving average
   ">",  # OBV trending up (accumulation)
       "<"   # OBV trending down (distribution)
        ],
  "usage_hint": "Look for divergence with price for reversal signals"
    },
    {
   "id": "roc",
        "name": "ROC (Rate of Change)",
        "category": CATEGORY_MOMENTUM,
  "range": {"bounded": False},
        "params": {
     "period": {"type": "int", "default": 12, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum oscillator measuring percentage change",
        "recommended_operators": [
            "crosses_above",  # ROC crosses above 0 (momentum turning positive)
         "crosses_below",  # ROC crosses below 0 (momentum turning negative)
">",  # ROC > 0 (positive momentum)
            "<"   # ROC < 0 (negative momentum)
        ],
        "typical_levels": {
            "zero_line": 0
        },
        "usage_hint": "Momentum indicator: positive ROC = uptrend, negative = downtrend"
    },
    {
        "id": "mfi",
   "name": "MFI (Money Flow Index)",
        "category": CATEGORY_VOLUME,
        "range": {"min": 0, "max": 100, "bounded": True},
        "params": {
            "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Volume-weighted RSI",
        "recommended_operators": [
  "crosses_above",  # MFI crosses above 20 (oversold → bullish)
      "crosses_below",  # MFI crosses below 80 (overbought → bearish)
   ">",  # MFI > 50 (buying pressure)
            "<",  # MFI < 20 (oversold)
            "between"# MFI between 20-80 (normal range)
        ],
        "typical_levels": {
            "oversold": 20,
   "neutral": 50,
            "overbought": 80
  },
  "usage_hint": "Similar to RSI but includes volume: better for volume-driven markets"
    }
]


def get_indicator_catalog():
    """Return full indicator catalog"""
    return INDICATOR_CATALOG


def get_indicator(indicator_id: str):
    """Get specific indicator by ID"""
    for ind in INDICATOR_CATALOG:
        if ind["id"] == indicator_id:
            return ind
    return None


def get_indicator_operators(indicator_id: str):
    """Get recommended operators for a specific indicator"""
    indicator = get_indicator(indicator_id)
    if not indicator:
        return None
    
    return {
     "indicator_id": indicator_id,
   "indicator_name": indicator["name"],
        "category": indicator["category"],
        "range": indicator.get("range", {}),
        "recommended_operators": indicator.get("recommended_operators", []),
        "typical_levels": indicator.get("typical_levels", {}),
        "usage_hint": indicator.get("usage_hint", "")
    }


def validate_indicator_params(indicator_id: str, params: dict):
    """Validate indicator parameters"""
    indicator = get_indicator(indicator_id)
    if not indicator:
        return False, f"Indicator {indicator_id} not found"
    
    for param_name, param_value in params.items():
        if param_name not in indicator["params"]:
            return False, f"Parameter {param_name} not found"
        
        param_spec = indicator["params"][param_name]
        param_type = param_spec["type"]
        
        if param_type == "int" and not isinstance(param_value, int):
            return False, f"Parameter {param_name} must be int"
        elif param_type == "float" and not isinstance(param_value, (int, float)):
            return False, f"Parameter {param_name} must be numeric"
        
        if "min" in param_spec and param_value < param_spec["min"]:
            return False, f"Parameter {param_name} must be >= {param_spec['min']}"
        if "max" in param_spec and param_value > param_spec["max"]:
            return False, f"Parameter {param_name} must be <= {param_spec['max']}"
    
    return True, "OK"