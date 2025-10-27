"""Feature calculation for Strategy Lab using pandas-ta"""
import pandas as pd
import numpy as np


def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators from OHLCV data
    
    Args:
        df: DataFrame with columns [ts, open, high, low, close, volume]
    
    Returns:
        DataFrame with calculated features
    """
    if len(df) < 200:
        raise ValueError(f"Need at least 200 candles for feature calculation, got {len(df)}")
    
    df = df.copy()
    df = df.sort_values('ts')
    
    # Basic price data
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    features = pd.DataFrame()
    features['ts'] = df['ts']
    features['close'] = close
    features['volume'] = volume
    
    # RSI
    features['rsi_14'] = calculate_rsi(close, 14)
    features['rsi_7'] = calculate_rsi(close, 7)
    
    # Moving Averages - EMA
    features['ema_20'] = close.ewm(span=20, adjust=False).mean()
    features['ema_50'] = close.ewm(span=50, adjust=False).mean()
    features['ema_200'] = close.ewm(span=200, adjust=False).mean()
    
    # Moving Averages - SMA
    features['sma_20'] = close.rolling(window=20).mean()
    features['sma_50'] = close.rolling(window=50).mean()
    features['sma_200'] = close.rolling(window=200).mean()
    
    # ATR
    features['atr_14'] = calculate_atr(df, 14)
    
    # ADX
    features['adx_14'] = calculate_adx(df, 14)
    
    # Bollinger Bands
    bb = calculate_bollinger_bands(close, 20, 2.0)
    features['bb_upper'] = bb['upper']
    features['bb_middle'] = bb['middle']
    features['bb_lower'] = bb['lower']
    
    # MACD
    macd = calculate_macd(close, 12, 26, 9)
    features['macd'] = macd['macd']
    features['macd_signal'] = macd['signal']
    features['macd_hist'] = macd['hist']
    
    return features


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate +DM and -DM
    high_diff = high.diff()
    low_diff = -low.diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    # Calculate ATR
    atr = calculate_atr(df, period)
    
    # Calculate +DI and -DI
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    # Calculate DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> dict:
    """Calculate Bollinger Bands"""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Calculate MACD indicator"""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'hist': histogram
    }


def features_to_rows(features_df: pd.DataFrame) -> list:
    """Convert features DataFrame to list of tuples for SQL insertion"""
    # Ensure all feature columns exist
    expected_cols = [
        'ts', 'close', 'volume', 'rsi_14', 'rsi_7',
        'ema_20', 'ema_50', 'ema_200',
        'sma_20', 'sma_50', 'sma_200',
        'atr_14', 'adx_14',
        'bb_upper', 'bb_middle', 'bb_lower',
        'macd', 'macd_signal', 'macd_hist'
    ]
    
    rows = []
    for _, row in features_df.iterrows():
        row_data = tuple(
            float(row[col]) if pd.notna(row[col]) else None
            for col in expected_cols
        )
        rows.append(row_data)
    
    return rows