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
    
    # Williams %R
    features['williams_r'] = calculate_williams_r(df, 14)
    
    # Stochastic
    stoch = calculate_stochastic(df, 14, 3)
    features['stoch_k'] = stoch['k']
    features['stoch_d'] = stoch['d']
    
    # Moving Averages - EMA
    features['ema_20'] = close.ewm(span=20, adjust=False).mean()
    features['ema_50'] = close.ewm(span=50, adjust=False).mean()
    features['ema_200'] = close.ewm(span=200, adjust=False).mean()
    
    # Moving Averages - SMA
    features['sma_20'] = close.rolling(window=20).mean()
    features['sma_50'] = close.rolling(window=50).mean()
    features['sma_200'] = close.rolling(window=200).mean()
    
    # SuperTrend
    supertrend = calculate_supertrend(df, 10, 3.0)
    features['supertrend'] = supertrend['supertrend']
    features['supertrend_direction'] = supertrend['direction']
    
    # ATR
    features['atr_14'] = calculate_atr(df, 14)
    
    # ADX
    features['adx_14'] = calculate_adx(df, 14)
    
    # CCI
    features['cci_20'] = calculate_cci(df, 20)
    
    # Bollinger Bands
    bb = calculate_bollinger_bands(close, 20, 2.0)
    features['bb_upper'] = bb['upper']
    features['bb_middle'] = bb['middle']
    features['bb_lower'] = bb['lower']
    
    # Keltner Channels
    keltner = calculate_keltner_channels(df, 20, 2.0)
    features['keltner_upper'] = keltner['upper']
    features['keltner_middle'] = keltner['middle']
    features['keltner_lower'] = keltner['lower']
    
    # Donchian Channels
    donchian = calculate_donchian_channels(df, 20)
    features['donchian_upper'] = donchian['upper']
    features['donchian_middle'] = donchian['middle']
    features['donchian_lower'] = donchian['lower']
    
    # MACD
    macd = calculate_macd(close, 12, 26, 9)
    features['macd'] = macd['macd']
    features['macd_signal'] = macd['signal']
    features['macd_hist'] = macd['hist']
    
    # VWAP
    features['vwap'] = calculate_vwap(df)
    
    # OBV
    features['obv'] = calculate_obv(df)
    
    # ROC
    features['roc_12'] = calculate_roc(df, 12)
    
    # MFI
    features['mfi_14'] = calculate_mfi(df, 14)
    
    return features


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Williams %R indicator
    
    Williams %R = -100 * (Highest High - Close) / (Highest High - Lowest Low)
    Range: -100 to 0
    - Values from 0 to -20 indicate overbought
    - Values from -80 to -100 indicate oversold
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    
    williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
    
    return williams_r


def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> dict:
    """
    Calculate Stochastic Oscillator
    
    %K = 100 * (Close - Lowest Low) / (Highest High - Lowest Low)
    %D = SMA(%K, d_period)
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    stoch_d = stoch_k.rolling(window=d_period).mean()
    
    return {
        'k': stoch_k,
        'd': stoch_d
    }


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> dict:
    """
    Calculate SuperTrend indicator
    
    Returns supertrend line and direction (+1 = uptrend, -1 = downtrend)
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate ATR
    atr = calculate_atr(df, period)
    
    # Calculate basic bands
    hl_avg = (high + low) / 2
    upper_band = hl_avg + (multiplier * atr)
    lower_band = hl_avg - (multiplier * atr)
    
    # Initialize supertrend
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    
    supertrend.iloc[0] = upper_band.iloc[0]
    direction.iloc[0] = 1
    
    for i in range(1, len(df)):
        # Determine trend
        if close.iloc[i] > supertrend.iloc[i-1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < supertrend.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]
        
        # Calculate supertrend value
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower_band.iloc[i]
            if supertrend.iloc[i] < supertrend.iloc[i-1]:
                supertrend.iloc[i] = supertrend.iloc[i-1]
        else:
            supertrend.iloc[i] = upper_band.iloc[i]
            if supertrend.iloc[i] > supertrend.iloc[i-1]:
                supertrend.iloc[i] = supertrend.iloc[i-1]
    
    return {
        'supertrend': supertrend,
        'direction': direction
    }


def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Calculate Commodity Channel Index (CCI)
    
    CCI = (Typical Price - SMA) / (0.015 * Mean Deviation)
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    typical_price = (high + low + close) / 3
    sma_tp = typical_price.rolling(window=period).mean()
    
    mean_deviation = typical_price.rolling(window=period).apply(
        lambda x: np.abs(x - x.mean()).mean()
    )
    
    cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
    
    return cci


def calculate_keltner_channels(df: pd.DataFrame, period: int = 20, multiplier: float = 2.0) -> dict:
    """
    Calculate Keltner Channels
    
    Middle = EMA(close, period)
    Upper = Middle + (multiplier * ATR)
    Lower = Middle - (multiplier * ATR)
    """
    close = df['close']
    
    middle = close.ewm(span=period, adjust=False).mean()
    atr = calculate_atr(df, period)
    
    upper = middle + (multiplier * atr)
    lower = middle - (multiplier * atr)
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def calculate_donchian_channels(df: pd.DataFrame, period: int = 20) -> dict:
    """
    Calculate Donchian Channels
    
    Upper = Highest High over period
    Lower = Lowest Low over period
    Middle = (Upper + Lower) / 2
    """
    high = df['high']
    low = df['low']
    
    upper = high.rolling(window=period).max()
    lower = low.rolling(window=period).min()
    middle = (upper + lower) / 2
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Volume Weighted Average Price (VWAP)
    
    VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
    
    Note: Resets daily in production, but here we calculate for entire period
    """
    high = df['high']
    low = df['low']
    close = df['close']
    volume = df['volume']
    
    typical_price = (high + low + close) / 3
    
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    
    return vwap


def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV)
    
    If close > previous close: OBV = previous OBV + volume
    If close < previous close: OBV = previous OBV - volume
    If close == previous close: OBV = previous OBV
    """
    close = df['close']
    volume = df['volume']
    
    obv = pd.Series(index=df.index, dtype=float)
    obv.iloc[0] = volume.iloc[0]
    
    for i in range(1, len(df)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]
    
    return obv


def calculate_roc(df: pd.DataFrame, period: int = 12) -> pd.Series:
    """
    Calculate Rate of Change (ROC)
    
    ROC = ((Close - Close[period ago]) / Close[period ago]) * 100
    """
    close = df['close']
    
    roc = ((close - close.shift(period)) / close.shift(period)) * 100
    
    return roc


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Money Flow Index (MFI) - Volume-weighted RSI
    
    1. Typical Price = (High + Low + Close) / 3
    2. Raw Money Flow = Typical Price * Volume
    3. Money Flow Ratio = (Positive Money Flow) / (Negative Money Flow)
    4. MFI = 100 - (100 / (1 + Money Flow Ratio))
    """
    high = df['high']
    low = df['low']
    close = df['close']
    volume = df['volume']
    
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume
    
    # Determine positive and negative money flow
    positive_flow = pd.Series(index=df.index, dtype=float)
    negative_flow = pd.Series(index=df.index, dtype=float)
    
    positive_flow.iloc[0] = 0
    negative_flow.iloc[0] = 0
    
    for i in range(1, len(df)):
        if typical_price.iloc[i] > typical_price.iloc[i-1]:
            positive_flow.iloc[i] = raw_money_flow.iloc[i]
            negative_flow.iloc[i] = 0
        elif typical_price.iloc[i] < typical_price.iloc[i-1]:
            positive_flow.iloc[i] = 0
            negative_flow.iloc[i] = raw_money_flow.iloc[i]
        else:
            positive_flow.iloc[i] = 0
            negative_flow.iloc[i] = 0
    
    # Calculate MFI
    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()
    
    mfi = 100 - (100 / (1 + (positive_mf / (negative_mf + 1e-10))))
    
    return mfi


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
        'ts', 'close', 'volume',
        'rsi_14', 'rsi_7', 'williams_r',
        'stoch_k', 'stoch_d',
        'ema_20', 'ema_50', 'ema_200',
        'sma_20', 'sma_50', 'sma_200',
        'supertrend', 'supertrend_direction',
        'atr_14', 'adx_14', 'cci_20',
        'bb_upper', 'bb_middle', 'bb_lower',
        'keltner_upper', 'keltner_middle', 'keltner_lower',
        'donchian_upper', 'donchian_middle', 'donchian_lower',
        'macd', 'macd_signal', 'macd_hist',
        'vwap', 'obv', 'roc_12', 'mfi_14'
    ]
    
    rows = []
    for _, row in features_df.iterrows():
        row_data = tuple(
            float(row[col]) if pd.notna(row[col]) else None
            for col in expected_cols
        )
        rows.append(row_data)
    
    return rows