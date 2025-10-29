"""
Market data tool using ccxt with robust fetching, caching and normalization
"""

import ccxt
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
from collections import OrderedDict
import time
import hashlib

from ..schemas import Candle
from ..config import AgentConfig


class SymbolNormalizer:
    """
    Normalize symbol formats for different exchanges
    
    Bitget: uses "BTC/USDT:USDT" for USDT-margined perps
    Binance: uses "BTC/USDT" for futures (with defaultType: future)
    """
    
    @staticmethod
    def normalize(symbol: str, exchange_name: str) -> str:
        """
        Normalize symbol to exchange-specific format
        
        Args:
            symbol: Input symbol (e.g., "BTC/USDT", "BTCUSDT", "BTC/USDT:USDT")
            exchange_name: "bitget" or "binance"
        
        Returns:
            Normalized symbol string
        """
        # Remove spaces and convert to uppercase
        symbol = symbol.replace(" ", "").upper()
        
        # Handle different input formats
        if exchange_name == "bitget":
            # Bitget requires "BTC/USDT:USDT" format for perps
            if ":" not in symbol:
                # Convert "BTC/USDT" -> "BTC/USDT:USDT"
                if "/" in symbol:
                    base_quote = symbol
                else:
                    # Convert "BTCUSDT" -> "BTC/USDT"
                    if symbol.endswith("USDT"):
                        base = symbol[:-4]
                        base_quote = f"{base}/USDT"
                    else:
                        raise ValueError(f"Cannot parse symbol: {symbol}")
                
                return f"{base_quote}:USDT"
            return symbol
        
        elif exchange_name == "binance":
            # Binance futures use "BTC/USDT" format (no settlement currency)
            if ":" in symbol:
                # Convert "BTC/USDT:USDT" -> "BTC/USDT"
                symbol = symbol.split(":")[0]
            
            if "/" not in symbol:
                # Convert "BTCUSDT" -> "BTC/USDT"
                if symbol.endswith("USDT"):
                    base = symbol[:-4]
                    symbol = f"{base}/USDT"
            
            return symbol
        
        else:
            raise ValueError(f"Unsupported exchange: {exchange_name}")
    
    @staticmethod
    def validate(symbol: str, exchange: ccxt.Exchange) -> bool:
        """Check if symbol exists on exchange"""
        try:
            markets = exchange.load_markets()
            return symbol in markets
        except Exception:
            return False


class CandleCache:
    """
    LRU cache with TTL for candle data
    
    Stores candles in memory with automatic expiration
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 10):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
    
    def _make_key(self, exchange: str, symbol: str, timeframe: str, lookback: int) -> str:
        """Generate cache key"""
        key_str = f"{exchange}:{symbol}:{timeframe}:{lookback}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, exchange: str, symbol: str, timeframe: str, lookback: int) -> Optional[List[Candle]]:
        """Get cached candles if not expired"""
        key = self._make_key(exchange, symbol, timeframe, lookback)
        
        if key not in self._cache:
            return None
        
        # Check TTL
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        # Move to end (LRU)
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def put(self, exchange: str, symbol: str, timeframe: str, lookback: int, candles: List[Candle]):
        """Store candles in cache"""
        key = self._make_key(exchange, symbol, timeframe, lookback)
        
        # Remove oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
        
        self._cache[key] = candles
        self._timestamps[key] = time.time()
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._timestamps.clear()


class MarketDataTool:
    """
    Robust market data fetcher with:
    - Symbol normalization
    - Exponential backoff retry
    - Gap detection and forward-fill
    - LRU cache with TTL
    - Incremental tail fetch
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        
        # Initialize exchange
        if config.exchange == "bitget":
            self.exchange = ccxt.bitget({
                "options": {"defaultType": "swap"},
                "enableRateLimit": True,
                "rateLimit": 100  # ms between requests
            })
        elif config.exchange == "binance":
            self.exchange = ccxt.binance({
                "options": {"defaultType": "future"},
                "enableRateLimit": True,
                "rateLimit": 50
            })
        else:
            raise ValueError(f"Unsupported exchange: {config.exchange}")
        
        # Load markets
        try:
            self.exchange.load_markets()
        except Exception as e:
            print(f"[MarketData] Warning: Could not load markets: {e}")
        
        # Initialize cache
        self.cache = CandleCache(max_size=100, ttl_seconds=5)
        
        # Symbol normalizer
        self.normalizer = SymbolNormalizer()
        
        # Last fetch timestamps for incremental fetch
        self._last_fetch: Dict[str, int] = {}
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for current exchange"""
        return self.normalizer.normalize(symbol, self.config.exchange)
    
    def _retry_with_backoff(self, func, *args, max_retries: int = 3, **kwargs):
        """
        Execute function with exponential backoff retry
        
        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Function result
        
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            
            except ccxt.RateLimitExceeded as e:
                wait_time = (2 ** attempt) * 1.0  # 1s, 2s, 4s
                print(f"[MarketData] Rate limit exceeded, waiting {wait_time}s...")
                time.sleep(wait_time)
                last_exception = e
            
            except ccxt.NetworkError as e:
                wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                print(f"[MarketData] Network error, retrying in {wait_time}s...")
                time.sleep(wait_time)
                last_exception = e
            
            except ccxt.ExchangeError as e:
                # Don't retry on exchange errors (invalid symbol, etc)
                print(f"[MarketData] Exchange error: {e}")
                raise
            
            except Exception as e:
                print(f"[MarketData] Unexpected error: {e}")
                last_exception = e
                break
        
        if last_exception:
            raise last_exception
    
    def _timeframe_to_seconds(self, timeframe: str) -> int:
        """Convert timeframe string to seconds"""
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        
        if unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        else:
            raise ValueError(f"Unsupported timeframe unit: {unit}")
    
    def _detect_and_fill_gaps(self, candles: List[Candle], timeframe: str) -> List[Candle]:
        """
        Detect gaps in candle data and forward-fill
        
        Args:
            candles: List of candles (must be sorted by timestamp)
            timeframe: Candle timeframe for gap detection
        
        Returns:
            List of candles with gaps filled
        """
        if not candles or len(candles) < 2:
            return candles
        
        tf_seconds = self._timeframe_to_seconds(timeframe)
        tf_ms = tf_seconds * 1000
        
        filled_candles = []
        
        for i in range(len(candles)):
            filled_candles.append(candles[i])
            
            # Check gap to next candle
            if i < len(candles) - 1:
                current_ts = candles[i].ts
                next_ts = candles[i + 1].ts
                expected_next_ts = current_ts + tf_ms
                
                # Gap detected
                while expected_next_ts < next_ts:
                    # Forward-fill: copy previous candle with new timestamp
                    gap_candle = Candle(
                        ts=expected_next_ts,
                        open=candles[i].close,
                        high=candles[i].close,
                        low=candles[i].close,
                        close=candles[i].close,
                        volume=0.0  # No volume during gap
                    )
                    filled_candles.append(gap_candle)
                    expected_next_ts += tf_ms
        
        return filled_candles
    
    def fetch_ohlcv_paginated(self, symbol: str, timeframe: str, 
                              lookback: int, max_requests: int = 10) -> List[Candle]:
        """
        Fetch OHLCV with pagination to get required lookback
        
        Args:
            symbol: Normalized symbol
            timeframe: Candle timeframe
            lookback: Number of candles needed
            max_requests: Maximum API requests to prevent infinite loops
        
        Returns:
            List of Candle objects (sorted by timestamp, oldest first)
        """
        all_candles = []
        requests_made = 0
        
        # Calculate time window
        tf_seconds = self._timeframe_to_seconds(timeframe)
        tf_ms = tf_seconds * 1000
        
        # Start from now
        since = int(time.time() * 1000) - (lookback * tf_ms)
        
        while len(all_candles) < lookback and requests_made < max_requests:
            # Fetch batch
            limit = min(1000, lookback - len(all_candles) + 100)  # Fetch extra to ensure coverage
            
            try:
                raw_candles = self._retry_with_backoff(
                    self.exchange.fetch_ohlcv,
                    symbol=symbol,
                    timeframe=timeframe,
                    since=since,
                    limit=limit
                )
                
                if not raw_candles:
                    break
                
                # Convert to Candle objects
                batch = [
                    Candle(
                        ts=int(c[0]),
                        open=float(c[1]),
                        high=float(c[2]),
                        low=float(c[3]),
                        close=float(c[4]),
                        volume=float(c[5])
                    )
                    for c in raw_candles
                ]
                
                all_candles.extend(batch)
                requests_made += 1
                
                # Update since for next page
                if batch:
                    since = batch[-1].ts + tf_ms
                
                # If we got less than limit, we've reached the end
                if len(batch) < limit:
                    break
            
            except Exception as e:
                print(f"[MarketData] Error in pagination: {e}")
                break
        
        # Remove duplicates (can happen at boundaries)
        seen_ts = set()
        unique_candles = []
        for candle in all_candles:
            if candle.ts not in seen_ts:
                seen_ts.add(candle.ts)
                unique_candles.append(candle)
        
        # Sort by timestamp
        unique_candles.sort(key=lambda c: c.ts)
        
        # Take only the most recent lookback candles
        return unique_candles[-lookback:] if len(unique_candles) > lookback else unique_candles
    
    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int = 100) -> List[Candle]:
        """
        Get recent N bars with intelligent caching and incremental fetch
        
        Args:
            symbol: Trading pair (will be normalized)
            timeframe: Candle timeframe
            lookback: Number of bars to fetch
        
        Returns:
            List of recent Candle objects (sorted by timestamp)
        """
        # Normalize symbol
        normalized_symbol = self._normalize_symbol(symbol)
        
        # Check cache first
        cached = self.cache.get(self.config.exchange, normalized_symbol, timeframe, lookback)
        if cached is not None:
            return cached
        
        # Fetch with pagination
        try:
            candles = self.fetch_ohlcv_paginated(normalized_symbol, timeframe, lookback)
            
            # Fill gaps
            candles = self._detect_and_fill_gaps(candles, timeframe)
            
            # Store in cache
            self.cache.put(self.config.exchange, normalized_symbol, timeframe, lookback, candles)
            
            # Update last fetch timestamp
            cache_key = f"{normalized_symbol}:{timeframe}"
            self._last_fetch[cache_key] = candles[-1].ts if candles else 0
            
            return candles
        
        except Exception as e:
            print(f"[MarketData] Failed to fetch {normalized_symbol}: {e}")
            return []
    
    def get_recent_bars_df(self, symbol: str, timeframe: str, lookback: int = 100) -> pd.DataFrame:
        """
        Get recent bars as pandas DataFrame
        
        Args:
            symbol: Trading pair
            timeframe: Candle timeframe
            lookback: Number of bars
        
        Returns:
            DataFrame with columns [ts, open, high, low, close, volume]
        """
        candles = self.get_recent_bars(symbol, timeframe, lookback)
        
        if not candles:
            return pd.DataFrame(columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
        
        df = pd.DataFrame([c.dict() for c in candles])
        df['datetime'] = pd.to_datetime(df['ts'], unit='ms')
        
        return df
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current ticker (price, volume, etc.)"""
        normalized_symbol = self._normalize_symbol(symbol)
        
        try:
            return self._retry_with_backoff(self.exchange.fetch_ticker, normalized_symbol)
        except Exception as e:
            print(f"[MarketData] Error fetching ticker for {normalized_symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        ticker = self.get_ticker(symbol)
        return float(ticker['last']) if ticker and 'last' in ticker else None
    
    def fetch_incremental(self, symbol: str, timeframe: str) -> List[Candle]:
        """
        Fetch only new candles since last fetch (tail fetch)
        
        Args:
            symbol: Trading pair
            timeframe: Candle timeframe
        
        Returns:
            List of new candles since last fetch
        """
        normalized_symbol = self._normalize_symbol(symbol)
        cache_key = f"{normalized_symbol}:{timeframe}"
        
        # Get last fetch timestamp
        since = self._last_fetch.get(cache_key)
        
        if since is None:
            # No previous fetch, return empty (use get_recent_bars for initial fetch)
            return []
        
        try:
            # Fetch only new candles
            raw_candles = self._retry_with_backoff(
                self.exchange.fetch_ohlcv,
                symbol=normalized_symbol,
                timeframe=timeframe,
                since=since,
                limit=100
            )
            
            if not raw_candles:
                return []
            
            candles = [
                Candle(
                    ts=int(c[0]),
                    open=float(c[1]),
                    high=float(c[2]),
                    low=float(c[3]),
                    close=float(c[4]),
                    volume=float(c[5])
                )
                for c in raw_candles
            ]
            
            # Update last fetch timestamp
            if candles:
                self._last_fetch[cache_key] = candles[-1].ts
            
            return candles
        
        except Exception as e:
            print(f"[MarketData] Error in incremental fetch: {e}")
            return []