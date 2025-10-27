"""Indicator catalog for Strategy Lab"""

INDICATOR_CATALOG = [
    {
        "id": "rsi",
        "name": "RSI (Relative Strength Index)",
        "params": {
            "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum oscillator measuring speed and change of price movements"
    },
    {
        "id": "stoch",
        "name": "Stochastic Oscillator",
        "params": {
            "k_period": {"type": "int", "default": 14, "min": 2, "max": 100},
            "d_period": {"type": "int", "default": 3, "min": 2, "max": 50},
            "smooth_k": {"type": "int", "default": 3, "min": 1, "max": 10}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum indicator comparing closing price to price range"
    },
    {
        "id": "macd",
        "name": "MACD (Moving Average Convergence Divergence)",
        "params": {
            "fast": {"type": "int", "default": 12, "min": 2, "max": 50},
            "slow": {"type": "int", "default": 26, "min": 2, "max": 100},
            "signal": {"type": "int", "default": 9, "min": 2, "max": 50}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Trend-following momentum indicator"
    },
    {
        "id": "ema",
        "name": "EMA (Exponential Moving Average)",
        "params": {
            "period": {"type": "int", "default": 20, "min": 2, "max": 500}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Moving average giving more weight to recent prices"
    },
    {
        "id": "sma",
        "name": "SMA (Simple Moving Average)",
        "params": {
            "period": {"type": "int", "default": 20, "min": 2, "max": 500}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Arithmetic mean of prices"
    },
    {
        "id": "atr",
        "name": "ATR (Average True Range)",
        "params": {
            "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Volatility indicator"
    },
    {
        "id": "adx",
        "name": "ADX (Average Directional Index)",
        "params": {
            "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Trend strength indicator"
    },
    {
        "id": "cci",
        "name": "CCI (Commodity Channel Index)",
        "params": {
            "period": {"type": "int", "default": 20, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum oscillator"
    },
    {
        "id": "bollinger",
        "name": "Bollinger Bands",
        "params": {
            "period": {"type": "int", "default": 20, "min": 2, "max": 100},
            "std_dev": {"type": "float", "default": 2.0, "min": 0.5, "max": 5.0}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Volatility bands"
    },
    {
        "id": "keltner",
        "name": "Keltner Channels",
        "params": {
            "period": {"type": "int", "default": 20, "min": 2, "max": 100},
            "atr_mult": {"type": "float", "default": 2.0, "min": 0.5, "max": 5.0}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Volatility-based envelopes"
    },
    {
        "id": "supertrend",
        "name": "Supertrend",
        "params": {
            "period": {"type": "int", "default": 10, "min": 2, "max": 50},
            "multiplier": {"type": "float", "default": 3.0, "min": 1.0, "max": 10.0}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Trend-following indicator based on ATR"
    },
    {
        "id": "donchian",
        "name": "Donchian Channels",
        "params": {
            "period": {"type": "int", "default": 20, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Channel formed by highest high and lowest low"
    },
    {
        "id": "vwap",
        "name": "VWAP (Volume Weighted Average Price)",
        "params": {},
        "supported_timeframes": ["5m", "15m", "1h"],
        "description": "Average price weighted by volume"
    },
    {
        "id": "obv",
        "name": "OBV (On Balance Volume)",
        "params": {},
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum indicator relating volume to price"
    },
    {
        "id": "roc",
        "name": "ROC (Rate of Change)",
        "params": {
            "period": {"type": "int", "default": 12, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum oscillator measuring percentage change"
    },
    {
        "id": "mfi",
        "name": "MFI (Money Flow Index)",
        "params": {
            "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Volume-weighted RSI"
    },
    {
        "id": "williams_r",
        "name": "Williams %R",
        "params": {
            "period": {"type": "int", "default": 14, "min": 2, "max": 100}
        },
        "supported_timeframes": ["5m", "15m", "1h", "4h", "1d"],
        "description": "Momentum indicator measuring overbought/oversold"
    }
]


def get_indicator_catalog():
    return INDICATOR_CATALOG


def get_indicator(indicator_id: str):
    for ind in INDICATOR_CATALOG:
        if ind["id"] == indicator_id:
            return ind
    return None


def validate_indicator_params(indicator_id: str, params: dict):
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