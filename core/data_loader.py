"""
Data Loader with Auto-Fetch

Loads OHLCV data from database.
If data doesn't exist, automatically fetches from exchange.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple
import sqlite3
import os
import ccxt
from ccxt.base.errors import RateLimitExceeded, NetworkError, ExchangeNotAvailable
import time


def find_db_file(exchange: str, symbol: str, timeframe: str) -> Optional[str]:
    """
    Find database file for symbol
    
    Searches in common locations and constructs path if needed.
    """
    
    # Normalize symbol for filename
    symbol_normalized = symbol.replace('/', '_').replace(':', '_')
    
    # Common patterns
    patterns = [
        f"data/market_data/{exchange}/{symbol_normalized}_{timeframe}.db",
        f"data/{exchange}_{symbol_normalized}_{timeframe}.db",
        f"{exchange}_{symbol_normalized}_{timeframe}.db",
        f"data/market_data/{exchange}/{timeframe}/{symbol_normalized}.db",
        f"data/candles_{timeframe}.db",
    ]
    
    # Check existing
    for pattern in patterns:
        if os.path.exists(pattern):
            return pattern
    
    # Construct default path
    default_path = f"data/market_data/{exchange}/{symbol_normalized}_{timeframe}.db"
    os.makedirs(os.path.dirname(default_path), exist_ok=True)
    
    return default_path


def fetch_from_exchange(
    exchange: str,
    symbol: str,
    timeframe: str,
    days: int,
    end_date: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Fetch OHLCV data from exchange with robust error handling
    
    Args:
        exchange: Exchange name ('bitget', 'binance')
        symbol: Symbol (e.g., 'BTC/USDT:USDT')
        timeframe: Timeframe (e.g., '5m')
        days: Number of days to fetch
        end_date: End date (default: now)
    
    Returns:
        DataFrame with OHLCV data
    """
    
    print(f"📡 Fetching data from {exchange}...")
    print(f"   Symbol: {symbol}")
    print(f"   Timeframe: {timeframe}")
    print(f"   Days: {days}")
    
    # Initialize exchange
    if exchange.lower() == 'bitget':
        ex = ccxt.bitget({
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True
        })
    elif exchange.lower() == 'binance':
        ex = ccxt.binance({
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")
    
    # Calculate date range
    if end_date is None:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days)
    since_ms = int(start_date.timestamp() * 1000)
    until_ms = int(end_date.timestamp() * 1000)
    
    # Get timeframe in milliseconds
    tf_ms = ex.parse_timeframe(timeframe) * 1000
    
    # Fetch with pagination
    all_candles = []
    current_since = since_ms
    max_retries = 3
    retries = 0
    
    while current_since < until_ms:
        try:
            candles = ex.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=current_since,
                limit=1000
            )
            
            retries = 0  # Reset on success
            
            if not candles:
                break
            
            # Deduplicate
            candles.sort(key=lambda c: c[0])
            if all_candles:
                last_ts = all_candles[-1][0]
                candles = [c for c in candles if c[0] > last_ts]
                
                if not candles:
                    current_since += 1000 * tf_ms
                    continue
            
            all_candles.extend(candles)
            
            # Progress
            progress = len(all_candles)
            print(f"\r   Fetched: {progress} candles...", end='', flush=True)
            
            # Advance cursor
            last_ts = candles[-1][0]
            current_since = last_ts + 1
            
            # Break if reached end
            if last_ts >= until_ms:
                break
            
            # Rate limiting
            if ex.rateLimit:
                time.sleep(ex.rateLimit / 1000.0)
        
        except RateLimitExceeded:
            retries += 1
            if retries >= max_retries:
                raise
            wait = (ex.rateLimit / 1000.0) + 0.5
            print(f"\n   Rate limit, waiting {wait:.1f}s...")
            time.sleep(wait)
        
        except (NetworkError, ExchangeNotAvailable) as e:
            retries += 1
            if retries >= max_retries:
                raise
            print(f"\n   Network error, retrying... ({retries}/{max_retries})")
            time.sleep(2.0)
    
    print()  # New line after progress
    
    # Filter by range
    all_candles = [c for c in all_candles if since_ms <= c[0] < until_ms]
    
    if not all_candles:
        raise ValueError(f"No data fetched from {exchange} for {symbol}")
    
    # Convert to DataFrame
    df = pd.DataFrame(
        all_candles,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('datetime')
    df = df.drop('timestamp', axis=1)
    
    print(f"✅ Fetched {len(df)} candles from exchange")
    
    return df


def save_to_db(
    df: pd.DataFrame,
    db_path: str,
    timeframe: str
):
    """
    Save DataFrame to database
    
    Args:
        df: DataFrame with OHLCV data (datetime index)
        db_path: Path to database file
        timeframe: Timeframe (for table name)
    """
    
    # Create table name
    table_name = f'candles_{timeframe}'
    
    # Convert datetime index to timestamp
    df_save = df.copy()
    df_save['ts'] = (df_save.index.astype('int64') // 10**6).astype('int64')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # Create table if not exists
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            ts INTEGER PRIMARY KEY,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL
        )
    """)
    
    # Insert data (ignore duplicates)
    for _, row in df_save.iterrows():
        try:
            conn.execute(f"""
                INSERT OR IGNORE INTO {table_name} (ts, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                int(row['ts']),
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume'])
            ))
        except Exception:
            continue
    
    conn.commit()
    conn.close()
    
    print(f"💾 Saved {len(df)} candles to database: {db_path}")


def load_data_from_db(
    db_path: str,
    timeframe: str,
    days: int,
    end_date: Optional[datetime] = None
) -> Optional[pd.DataFrame]:
    """
    Load OHLCV data from database
    
    Returns:
        DataFrame or None if not found
    """
    
    if not os.path.exists(db_path):
        return None
    
    # Calculate date range
    if end_date is None:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days)
    start_ms = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)
    
    # Connect
    conn = sqlite3.connect(db_path)
    
    # Try different table names
    table_names = [
        f'candles_{timeframe}',
        'candles',
        'ohlcv',
        f'{timeframe}_candles'
    ]
    
    df = None
    
    for table_name in table_names:
        try:
            query = f"""
                SELECT ts, open, high, low, close, volume
                FROM {table_name}
                WHERE ts >= ? AND ts < ?
                ORDER BY ts ASC
            """
            
            df = pd.read_sql_query(query, conn, params=(start_ms, end_ms))
            
            if len(df) > 0:
                break
        
        except Exception:
            continue
    
    conn.close()
    
    if df is None or len(df) == 0:
        return None
    
    # Convert to datetime index
    df['datetime'] = pd.to_datetime(df['ts'], unit='ms')
    df = df.set_index('datetime')
    df = df.drop('ts', axis=1)
    
    return df


def load_data(
    exchange: str = 'bitget',
    symbol: str = 'BTC/USDT:USDT',
    timeframe: str = '5m',
    days: int = 90,
    auto_fetch: bool = True
) -> Tuple[pd.DataFrame, dict]:
    """
    Load data from database with automatic fetch if missing
    
    Args:
        exchange: Exchange name
        symbol: Symbol
        timeframe: Timeframe
        days: Number of days
        auto_fetch: If True, fetch from exchange if DB empty
    
    Returns:
        Tuple of (DataFrame, metadata_dict)
    """
    
    print("=" * 80)
    print("DATA LOADING")
    print("=" * 80)
    
    # Find or create DB path
    db_path = find_db_file(exchange, symbol, timeframe)
    
    print(f"📂 Database: {db_path}")
    
    # Try to load from database
    df = load_data_from_db(db_path, timeframe, days)
    
    if df is not None and len(df) >= 200:
        # Enough data in database
        metadata = {
            'exchange': exchange,
            'symbol': symbol,
            'timeframe': timeframe,
            'db_path': db_path,
            'start_date': df.index[0],
            'end_date': df.index[-1],
            'candles': len(df),
            'days_actual': (df.index[-1] - df.index[0]).days,
            'source': 'database'
        }
        
        print(f"✅ Loaded {len(df)} candles from database")
        print(f"   Period: {df.index[0]} to {df.index[-1]}")
        print(f"   Days: {metadata['days_actual']}")
        
        return df, metadata
    
    else:
        # Database empty or insufficient data
        if not auto_fetch:
            raise ValueError(f"No data in database and auto_fetch=False")
        
        print("⚠️  Database empty or insufficient data")
        print("📡 Fetching from exchange...")
        
        # Fetch from exchange
        df = fetch_from_exchange(exchange, symbol, timeframe, days)
        
        # Save to database
        save_to_db(df, db_path, timeframe)
        
        metadata = {
            'exchange': exchange,
            'symbol': symbol,
            'timeframe': timeframe,
            'db_path': db_path,
            'start_date': df.index[0],
            'end_date': df.index[-1],
            'candles': len(df),
            'days_actual': (df.index[-1] - df.index[0]).days,
            'source': 'exchange_fetch'
        }
        
        print(f"✅ Data ready: {len(df)} candles")
        
        return df, metadata


if __name__ == '__main__':
    print("✅ Testing Data Loader with Auto-Fetch...")
    
    # Test: Load BTC data (will fetch if not exists)
    print("\n" + "=" * 80)
    print("TEST: Load BTC/USDT:USDT data (auto-fetch if needed)")
    print("=" * 80)
    print()
    
    try:
        df, metadata = load_data(
            exchange='bitget',
            symbol='BTC/USDT:USDT',
            timeframe='5m',
            days=7,  # Small amount for testing
            auto_fetch=True
        )
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"\n📊 Data loaded:")
        print(f"   Shape: {df.shape}")
        print(f"   Source: {metadata['source']}")
        print(f"   Database: {metadata['db_path']}")
        print(f"   Period: {metadata['start_date']} to {metadata['end_date']}")
        
        print(f"\n📈 Price statistics:")
        print(f"   Min: ${df['close'].min():.2f}")
        print(f"   Max: ${df['close'].max():.2f}")
        print(f"   Last: ${df['close'].iloc[-1]:.2f}")
        
        print("\n✅ Test passed!")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()