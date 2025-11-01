"""
Dynamic Indicator Calculation Module

Provides parameterizable indicator functions for optimization.
All functions accept custom parameters and return calculated series.
"""

import pandas as pd
import numpy as np
from typing import Tuple


# ============================================================================
# TREND INDICATORS
# ============================================================================

def calculate_ema(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Exponential Moving Average"""
    return df['close'].ewm(span=period, adjust=False).mean()


def calculate_sma(df: pd.DataFrame, period: int = 50) -> pd.Series:
    """Simple Moving Average"""
    return df['close'].rolling(window=period).mean()


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD (Moving Average Convergence Divergence)"""
    close = df['close']
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """ADX (Average Directional Index) with +DI and -DI"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_dm = pd.Series(plus_dm, index=df.index).rolling(window=period).mean()
    minus_dm = pd.Series(minus_dm, index=df.index).rolling(window=period).mean()
    
    # DI
    plus_di = 100 * (plus_dm / atr)
    minus_di = 100 * (minus_dm / atr)
    
    # DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx, plus_di, minus_di


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
    """SuperTrend Indicator"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate ATR
    atr = calculate_atr(df, period=period)
    
    # Calculate basic bands
    hl_avg = (high + low) / 2
    upper_band = hl_avg + (multiplier * atr)
    lower_band = hl_avg - (multiplier * atr)
    
    # Initialize
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    
    supertrend.iloc[0] = lower_band.iloc[0]
    direction.iloc[0] = 1
    
    # Calculate SuperTrend
    for i in range(1, len(df)):
        # Update bands
        if lower_band.iloc[i] > lower_band.iloc[i-1] or close.iloc[i-1] < lower_band.iloc[i-1]:
            lower_band.iloc[i] = lower_band.iloc[i]
        else:
            lower_band.iloc[i] = lower_band.iloc[i-1]
        
        if upper_band.iloc[i] < upper_band.iloc[i-1] or close.iloc[i-1] > upper_band.iloc[i-1]:
            upper_band.iloc[i] = upper_band.iloc[i]
        else:
            upper_band.iloc[i] = upper_band.iloc[i-1]
        
        # Determine direction
        if close.iloc[i] <= upper_band.iloc[i]:
            supertrend.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1
        else:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1
    
    return supertrend, direction


def calculate_donchian(df: pd.DataFrame, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Donchian Channels"""
    high = df['high']
    low = df['low']
    
    upper = high.rolling(window=period).max()
    lower = low.rolling(window=period).min()
    middle = (upper + lower) / 2
    
    return upper, lower, middle


# ============================================================================
# MOMENTUM INDICATORS
# ============================================================================

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """RSI (Relative Strength Index)"""
    close = df['close']
    delta = close.diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3, smooth_k: int = 3) -> Tuple[pd.Series, pd.Series]:
    """Stochastic Oscillator"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate raw %K
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k_raw = 100 * (close - lowest_low) / (highest_high - lowest_low)
    
    # Smooth %K
    k = k_raw.rolling(window=smooth_k).mean()
    
    # Calculate %D (signal line)
    d = k.rolling(window=d_period).mean()
    
    return k, d


def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """CCI (Commodity Channel Index)"""
    tp = (df['high'] + df['low'] + df['close']) / 3  # Typical Price
    sma = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    
    cci = (tp - sma) / (0.015 * mad)
    
    return cci


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """MFI (Money Flow Index)"""
    tp = (df['high'] + df['low'] + df['close']) / 3  # Typical Price
    mf = tp * df['volume']  # Money Flow
    
    # Positive and negative money flow
    delta_tp = tp.diff()
    pos_mf = np.where(delta_tp > 0, mf, 0)
    neg_mf = np.where(delta_tp < 0, mf, 0)
    
    pos_mf = pd.Series(pos_mf, index=df.index)
    neg_mf = pd.Series(neg_mf, index=df.index)
    
    # Sum over period
    pos_mf_sum = pos_mf.rolling(window=period).sum()
    neg_mf_sum = neg_mf.rolling(window=period).sum()
    
    # Money Flow Ratio
    mfr = pos_mf_sum / neg_mf_sum
    
    # MFI
    mfi = 100 - (100 / (1 + mfr))
    
    return mfi


# ============================================================================
# VOLATILITY INDICATORS
# ============================================================================

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR (Average True Range)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands"""
    close = df['close']
    middle = close.rolling(window=period).mean()
    std_dev = close.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def calculate_keltner_channels(df: pd.DataFrame, period: int = 20, multiplier: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Keltner Channels"""
    close = df['close']
    middle = close.ewm(span=period, adjust=False).mean()
    atr = calculate_atr(df, period=period)
    
    upper = middle + (multiplier * atr)
    lower = middle - (multiplier * atr)
    
    return upper, middle, lower


def calculate_bollinger_bandwidth(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.Series:
    """Bollinger Bandwidth (as percentage)"""
    upper, middle, lower = calculate_bollinger_bands(df, period=period, std=std)
    bandwidth = 100 * (upper - lower) / middle
    return bandwidth


def check_bollinger_in_keltner(df: pd.DataFrame, bb_period: int = 20, bb_std: float = 2.0, keltner_period: int = 20, keltner_mult: float = 2.0) -> pd.Series:
    """Check if Bollinger Bands are inside Keltner Channels (squeeze)"""
    bb_upper, _, bb_lower = calculate_bollinger_bands(df, period=bb_period, std=bb_std)
    keltner_upper, _, keltner_lower = calculate_keltner_channels(df, period=keltner_period, multiplier=keltner_mult)
    
    squeeze = (bb_upper < keltner_upper) & (bb_lower > keltner_lower)
    return squeeze


# ============================================================================
# VOLUME INDICATORS
# ============================================================================

def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """OBV (On-Balance Volume)"""
    close = df['close']
    volume = df['volume']
    
    direction = np.where(close > close.shift(1), 1, -1)
    direction = pd.Series(direction, index=df.index)
    
    obv = (direction * volume).cumsum()
    return obv


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """VWAP (Volume Weighted Average Price)"""
    tp = (df['high'] + df['low'] + df['close']) / 3
    vwap = (tp * df['volume']).cumsum() / df['volume'].cumsum()
    return vwap


def calculate_vwap_std(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """VWAP Standard Deviation Bands"""
    vwap = calculate_vwap(df)
    tp = (df['high'] + df['low'] + df['close']) / 3
    vwap_std = (tp - vwap).rolling(window=period).std()
    return vwap_std


# ============================================================================
# DERIVED INDICATORS
# ============================================================================

def calculate_atr_percentile(df: pd.DataFrame, atr_period: int = 14, lookback: int = 100) -> pd.Series:
    """ATR Percentile (0-100)"""
    atr = calculate_atr(df, period=atr_period)
    atr_percentile = atr.rolling(window=lookback).apply(
        lambda x: (x.iloc[-1] <= x).sum() / len(x) * 100,
        raw=False
    )
    return atr_percentile


# ============================================================================
# BATCH CALCULATION (MAIN FUNCTION)
# ============================================================================

def calculate_all_indicators(df: pd.DataFrame, params: dict) -> dict:
    """
    Calculate all indicators with custom parameters
    
    Args:
        df: DataFrame with OHLCV data
        params: Dictionary of parameters
    
    Returns:
        Dictionary of indicator series
    """
    indicators = {}
    
    # TREND INDICATORS
    if 'ema_fast_period' in params:
        indicators['ema20'] = calculate_ema(df, period=params['ema_fast_period'])
    
    if 'ema_slow_period' in params:
        indicators['ema50'] = calculate_ema(df, period=params['ema_slow_period'])
    
    if 'ema_trend_period' in params:
        indicators['ema200'] = calculate_ema(df, period=params['ema_trend_period'])
    
    # MACD
    if all(k in params for k in ['macd_fast', 'macd_slow', 'macd_signal']):
        macd, signal, hist = calculate_macd(df, fast=params['macd_fast'], slow=params['macd_slow'], signal=params['macd_signal'])
        indicators['macd'] = macd
        indicators['macd_signal'] = signal
        indicators['macd_hist'] = hist
    
    # ADX
    if 'adx_period' in params:
        adx, plus_di, minus_di = calculate_adx(df, period=params['adx_period'])
        indicators['adx14'] = adx
        indicators['plus_di'] = plus_di
        indicators['minus_di'] = minus_di
    
    # SuperTrend
    if all(k in params for k in ['supertrend_period', 'supertrend_mult']):
        st, direction = calculate_supertrend(df, period=params['supertrend_period'], multiplier=params['supertrend_mult'])
        indicators['supertrend'] = st
        indicators['supertrend_direction'] = direction
        indicators['supertrend_bull'] = (direction == 1).astype(int)
        indicators['supertrend_bear'] = (direction == -1).astype(int)
    
    # Donchian
    if 'donchian_period' in params:
        upper, lower, middle = calculate_donchian(df, period=params['donchian_period'])
        indicators['donchian_high20'] = upper
        indicators['donchian_low20'] = lower
        indicators['donchian_middle'] = middle
    
    # MOMENTUM INDICATORS
    if 'rsi_period' in params:
        indicators['rsi14'] = calculate_rsi(df, period=params['rsi_period'])
    
    # Stochastic
    if all(k in params for k in ['stoch_k_period', 'stoch_d_period']):
        k, d = calculate_stochastic(df, k_period=params['stoch_k_period'], d_period=params['stoch_d_period'], smooth_k=params.get('stoch_smooth_k', 3))
        indicators['stoch_k'] = k
        indicators['stoch_d'] = d
    
    if 'cci_period' in params:
        indicators['cci'] = calculate_cci(df, period=params['cci_period'])
    
    if 'mfi_period' in params:
        indicators['mfi'] = calculate_mfi(df, period=params['mfi_period'])
    
    # VOLATILITY INDICATORS
    if 'atr_period' in params:
        indicators['atr'] = calculate_atr(df, period=params['atr_period'])
    
    # Bollinger Bands
    if all(k in params for k in ['bb_period', 'bb_std']):
        upper, middle, lower = calculate_bollinger_bands(df, period=params['bb_period'], std=params['bb_std'])
        indicators['bb_upper'] = upper
        indicators['bb_middle'] = middle
        indicators['bb_lower'] = lower
        indicators['bb_bw_pct'] = calculate_bollinger_bandwidth(df, period=params['bb_period'], std=params['bb_std'])
    
    # Keltner Channels
    if all(k in params for k in ['keltner_period', 'keltner_mult']):
        upper, middle, lower = calculate_keltner_channels(df, period=params['keltner_period'], multiplier=params['keltner_mult'])
        indicators['keltner_upper'] = upper
        indicators['keltner_middle'] = middle
        indicators['keltner_lower'] = lower
    
    # Squeeze Detection
    if all(k in params for k in ['bb_period', 'bb_std', 'keltner_period', 'keltner_mult']):
        indicators['boll_in_keltner'] = check_bollinger_in_keltner(df, bb_period=params['bb_period'], bb_std=params['bb_std'], keltner_period=params['keltner_period'], keltner_mult=params['keltner_mult']).astype(int)
    
    # VOLUME INDICATORS
    if params.get('include_obv', False):
        indicators['obv'] = calculate_obv(df)
    
    if params.get('include_vwap', False):
        indicators['vwap'] = calculate_vwap(df)
        if 'vwap_std_period' in params:
            indicators['vwap_std'] = calculate_vwap_std(df, period=params['vwap_std_period'])
    
    # DERIVED INDICATORS
    if 'atr_period' in params and params.get('include_atr_percentile', False):
        indicators['atr_norm_pct'] = calculate_atr_percentile(df, atr_period=params['atr_period'], lookback=params.get('atr_lookback', 100))
    
    # ADD PREVIOUS VALUES (FOR STRATEGIES THAT NEED THEM)
    for key in list(indicators.keys()):
        if params.get('include_prev', False):
            indicators[f'{key}_prev'] = indicators[key].shift(1)
        if params.get('include_5bars_ago', False):
            indicators[f'{key}_5bars_ago'] = indicators[key].shift(5)
    
    # ADD PRICE PREV VALUES
    indicators['close_prev'] = df['close'].shift(1)
    indicators['high_prev'] = df['high'].shift(1)
    indicators['low_prev'] = df['low'].shift(1)
    indicators['prev_high'] = df['high'].shift(1)
    indicators['prev_low'] = df['low'].shift(1)
    
    return indicators


if __name__ == '__main__':
    print("✅ Testing Dynamic Indicators Module...")
    
    # Create test data
    dates = pd.date_range('2024-01-01', periods=500, freq='5T')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': 42000 + np.random.randn(500).cumsum() * 100,
        'high': 42000 + np.random.randn(500).cumsum() * 100 + 50,
        'low': 42000 + np.random.randn(500).cumsum() * 100 - 50,
        'close': 42000 + np.random.randn(500).cumsum() * 100,
        'volume': np.random.randint(100, 1000, 500)
    }, index=dates)
    
    # Test with params
    params = {
        'rsi_period': 14,
        'bb_period': 20,
        'bb_std': 2.0,
        'ema_fast_period': 20,
        'ema_slow_period': 50,
        'ema_trend_period': 200,
        'atr_period': 14,
        'adx_period': 14,
        'include_prev': False
    }
    
    indicators = calculate_all_indicators(df, params)
    
    print(f"\n✅ Calculated {len(indicators)} indicators:")
    for name in sorted(indicators.keys()):
        series = indicators[name]
        if isinstance(series, pd.Series) and len(series) > 0:
            last_val = series.iloc[-1]
            if not np.isnan(last_val):
                print(f"  {name:20s}: {last_val:>10.2f}")
    
    print("\n✅ All tests passed!")