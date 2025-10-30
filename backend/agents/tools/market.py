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
        symbol = symbol.replace(" ", "").upper()
        
        if exchange_name == "bitget":
            if ":" not in symbol:
                if "/" in symbol:
                    base_quote = symbol
                else:
                    if symbol.endswith("USDT"):
                        base = symbol[:-4]
                        base_quote = f"{base}/USDT"
                    else:
                        raise ValueError(f"Cannot parse symbol: {symbol}")
                return f"{base_quote}:USDT"
            return symbol
        elif exchange_name == "binance":
            if ":" in symbol:
                symbol = symbol.split(":")[0]
            if "/" not in symbol:
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
    """LRU cache with TTL for candle data"""
    
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
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            del self._cache[key]
            del self._timestamps[key]
            return None
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def put(self, exchange: str, symbol: str, timeframe: str, lookback: int, candles: List[Candle]):
        """Store candles in cache"""
        key = self._make_key(exchange, symbol, timeframe, lookback)
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
    """Robust market data fetcher with automatic database persistence"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        
        if config.exchange == "bitget":
            self.exchange = ccxt.bitget({
                "options": {"defaultType": "swap"},
                "enableRateLimit": True,
                "rateLimit": 100
            })
        elif config.exchange == "binance":
            self.exchange = ccxt.binance({
                "options": {"defaultType": "future"},
                "enableRateLimit": True,
                "rateLimit": 50
            })
        else:
            raise ValueError(f"Unsupported exchange: {config.exchange}")
        
        try:
            self.exchange.load_markets()
        except Exception as e:
            print(f"[MarketData] Warning: Could not load markets: {e}")
        
        self.cache = CandleCache(max_size=100, ttl_seconds=5)
        self.normalizer = SymbolNormalizer()
        self._last_fetch: Dict[str, int] = {}
        self._db_enabled = True
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for current exchange"""
        return self.normalizer.normalize(symbol, self.config.exchange)
    
    def _retry_with_backoff(self, func, *args, max_retries: int = 3, **kwargs):
        """Execute function with exponential backoff retry"""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except ccxt.RateLimitExceeded as e:
                wait_time = (2 ** attempt) * 1.0
                print(f"[MarketData] Rate limit exceeded, waiting {wait_time}s...")
                time.sleep(wait_time)
                last_exception = e
            except ccxt.NetworkError as e:
                wait_time = (2 ** attempt) * 0.5
                print(f"[MarketData] Network error, retrying in {wait_time}s...")
                time.sleep(wait_time)
                last_exception = e
            except ccxt.ExchangeError as e:
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
        """Detect gaps in candle data and forward-fill"""
        if not candles or len(candles) < 2:
            return candles
        tf_seconds = self._timeframe_to_seconds(timeframe)
        tf_ms = tf_seconds * 1000
        filled_candles = []
        for i in range(len(candles)):
            filled_candles.append(candles[i])
            if i < len(candles) - 1:
                current_ts = candles[i].ts
                next_ts = candles[i + 1].ts
                expected_next_ts = current_ts + tf_ms
                while expected_next_ts < next_ts:
                    gap_candle = Candle(
                        ts=expected_next_ts,
                        open=candles[i].close,
                        high=candles[i].close,
                        low=candles[i].close,
                        close=candles[i].close,
                        volume=0.0
                    )
                    filled_candles.append(gap_candle)
                    expected_next_ts += tf_ms
        return filled_candles
    
    def fetch_ohlcv_paginated(self, symbol: str, timeframe: str, lookback: int, max_requests: int = 10) -> List[Candle]:
        """Fetch OHLCV with pagination to get required lookback"""
        all_candles = []
        requests_made = 0
        tf_seconds = self._timeframe_to_seconds(timeframe)
        tf_ms = tf_seconds * 1000
        since = int(time.time() * 1000) - (lookback * tf_ms)
        
        while len(all_candles) < lookback and requests_made < max_requests:
            limit = min(1000, lookback - len(all_candles) + 100)
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
                if batch:
                    since = batch[-1].ts + tf_ms
                if len(batch) < limit:
                    break
            except Exception as e:
                print(f"[MarketData] Error in pagination: {e}")
                break
        
        seen_ts = set()
        unique_candles = []
        for candle in all_candles:
            if candle.ts not in seen_ts:
                seen_ts.add(candle.ts)
                unique_candles.append(candle)
        unique_candles.sort(key=lambda c: c.ts)
        return unique_candles[-lookback:] if len(unique_candles) > lookback else unique_candles
    
    def _save_candles_to_db(self, symbol: str, timeframe: str, candles: List[Candle]):
        """Save candles to database"""
        try:
            import sqlite3
            import yaml
            import os
            cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
            db_path = cfg.get("db", {}).get("path")
            if not db_path:
                return
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS candles (
                ts INTEGER PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL
            )""")
            for candle in candles:
                cur.execute(
                    "INSERT OR IGNORE INTO candles (ts, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?)",
                    (candle.ts, candle.open, candle.high, candle.low, candle.close, candle.volume)
                )
            conn.commit()
            conn.close()
            print(f"[MarketData] Saved {len(candles)} candles to database")
        except Exception as e:
            print(f"[MarketData] Error saving to database: {e}")
    
    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int = 100) -> List[Candle]:
        """Get recent N bars with intelligent caching and incremental fetch"""
        normalized_symbol = self._normalize_symbol(symbol)
        cached = self.cache.get(self.config.exchange, normalized_symbol, timeframe, lookback)
        if cached is not None:
            return cached
        try:
            candles = self.fetch_ohlcv_paginated(normalized_symbol, timeframe, lookback)
            candles = self._detect_and_fill_gaps(candles, timeframe)
            if self._db_enabled and candles:
                self._save_candles_to_db(normalized_symbol, timeframe, candles)
            self.cache.put(self.config.exchange, normalized_symbol, timeframe, lookback, candles)
            cache_key = f"{normalized_symbol}:{timeframe}"
            self._last_fetch[cache_key] = candles[-1].ts if candles else 0
            return candles
        except Exception as e:
            print(f"[MarketData] Failed to fetch {normalized_symbol}: {e}")
            return []
    
    def get_recent_bars_df(self, symbol: str, timeframe: str, lookback: int = 100) -> pd.DataFrame:
        """Get recent bars as pandas DataFrame"""
        candles = self.get_recent_bars(symbol, timeframe, lookback)
        if not candles:
            return pd.DataFrame(columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
        df = pd.DataFrame([c.dict() for c in candles])
        df['datetime'] = pd.to_datetime(df['ts'], unit='ms')
        return df
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current ticker (price, volume, etc.)"""
        normalized_symbol = self._normalize_symbol(symbol)
        print(f"[MarketData] Fetching ticker for {normalized_symbol}...")
        try:
            ticker = self._retry_with_backoff(self.exchange.fetch_ticker, normalized_symbol)
            print(f"[MarketData] ✓ Ticker fetched successfully")
            return ticker
        except Exception as e:
            print(f"[MarketData] ✗ Error fetching ticker for {normalized_symbol}: {type(e).__name__}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            print(f"[MarketData] Getting price for {symbol} → {normalized_symbol}")
            ticker = self.get_ticker(normalized_symbol)
            if not ticker:
                print(f"[MarketData] ✗ Ticker is None for {normalized_symbol}")
                return None
            if 'last' not in ticker:
                print(f"[MarketData] ✗ No 'last' price in ticker: {ticker.keys()}")
                return None
            price = float(ticker['last'])
            print(f"[MarketData] ✓ Price for {normalized_symbol}: ${price:,.2f}")
            return price
        except Exception as e:
            print(f"[MarketData] ✗ Error getting price for {symbol}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def fetch_incremental(self, symbol: str, timeframe: str) -> List[Candle]:
        """Fetch only new candles since last fetch (tail fetch)"""
        normalized_symbol = self._normalize_symbol(symbol)
        cache_key = f"{normalized_symbol}:{timeframe}"
        since = self._last_fetch.get(cache_key)
        if since is None:
            return []
        try:
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
            if self._db_enabled and candles:
                self._save_candles_to_db(normalized_symbol, timeframe, candles)
            if candles:
                self._last_fetch[cache_key] = candles[-1].ts
            return candles
        except Exception as e:
            print(f"[MarketData] Error in incremental fetch: {e}")
            return []