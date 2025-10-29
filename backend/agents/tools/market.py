"""
Market data tool using ccxt
"""

import ccxt
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
from ..schemas import Candle
from ..config import AgentConfig


class MarketDataTool:
    """Fetch market data via ccxt REST API"""
    
    def __init__(self, config: AgentConfig):
   self.config = config
      
        # Initialize exchange
        if config.exchange == "bitget":
    self.exchange = ccxt.bitget({"options": {"defaultType": "swap"}})
        elif config.exchange == "binance":
   self.exchange = ccxt.binance({"options": {"defaultType": "future"}})
        else:
            raise ValueError(f"Unsupported exchange: {config.exchange}")
      
      self.exchange.enableRateLimit = True
   
    # Simple in-memory cache
      self._cache: Dict[str, Dict] = {}
        self._cache_ttl = 5  # seconds

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: Optional[int] = None, 
 limit: int = 100) -> List[Candle]:
        """
        Fetch OHLCV data
        
Args:
   symbol: Trading pair (e.g., "BTC/USDT:USDT")
   timeframe: Candle timeframe (e.g., "5m")
     since: Start timestamp in milliseconds
  limit: Number of candles to fetch
        
        Returns:
   List of Candle objects
        """
        try:
          raw_candles = self.exchange.fetch_ohlcv(
    symbol=symbol,
        timeframe=timeframe,
    since=since,
                limit=limit
            )
            
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

            return candles
        
        except Exception as e:
            print(f"[MarketData] Error fetching OHLCV for {symbol}: {e}")
         return []
  
    def get_recent_bars(self, symbol: str, timeframe: str, lookback: int = 100) -> List[Candle]:
    """
        Get recent N bars with caching
  
        Args:
       symbol: Trading pair
   timeframe: Candle timeframe
         lookback: Number of bars to fetch
        
        Returns:
  List of recent Candle objects
        """
        
        # Check cache
   cache_key = f"{symbol}:{timeframe}"
        now = time.time()
        
        if cache_key in self._cache:
  cached = self._cache[cache_key]
     if now - cached['timestamp'] < self._cache_ttl:
          return cached['data']
        
        # Fetch fresh data
        candles = self.fetch_ohlcv(symbol, timeframe, limit=lookback)
   
   # Update cache
        self._cache[cache_key] = {
         'timestamp': now,
     'data': candles
        }
        
        return candles
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
    """Get current ticker (price, volume, etc.)"""
 try:
         return self.exchange.fetch_ticker(symbol)
        except Exception as e:
          print(f"[MarketData] Error fetching ticker for {symbol}: {e}")
    return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
      ticker = self.get_ticker(symbol)
        return float(ticker['last']) if ticker else None
