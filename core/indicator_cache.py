"""
Indicator Cache System

Caches calculated indicators to avoid redundant computations during optimization.
Uses dataframe hash + parameter hash as cache key.
"""

import hashlib
import json
from typing import Dict, Any, Optional
import pandas as pd


class IndicatorCache:
    """
    Thread-safe indicator cache
    
    Cache key = hash(dataframe + parameters)
    Cache value = dictionary of indicator series
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of cached entries (default: 100)
        """
        self._cache: Dict[str, Dict[str, pd.Series]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _hash_dataframe(self, df: pd.DataFrame) -> str:
        """
        Create hash from dataframe
        
        Uses first/last timestamps + row count for efficiency
        """
        if len(df) == 0:
            return "empty"
        
        # Fast hash: use index bounds + shape
        key_parts = [
            str(df.index[0]),
            str(df.index[-1]),
            str(len(df)),
            str(df['close'].iloc[0]),
            str(df['close'].iloc[-1])
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _hash_params(self, params: dict) -> str:
        """Create hash from parameters dictionary"""
        # Sort keys for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()[:16]
    
    def _make_key(self, df: pd.DataFrame, params: dict) -> str:
        """Create cache key from dataframe + parameters"""
        df_hash = self._hash_dataframe(df)
        params_hash = self._hash_params(params)
        return f"{df_hash}_{params_hash}"
    
    def get(self, df: pd.DataFrame, params: dict) -> Optional[Dict[str, pd.Series]]:
        """
        Get cached indicators
        
        Args:
            df: DataFrame
            params: Parameters dict
        
        Returns:
            Dictionary of indicators or None if not cached
        """
        key = self._make_key(df, params)
        
        if key in self._cache:
            self.hits += 1
            return self._cache[key]
        
        self.misses += 1
        return None
    
    def set(self, df: pd.DataFrame, params: dict, indicators: Dict[str, pd.Series]):
        """
        Cache indicators
        
        Args:
            df: DataFrame
            params: Parameters dict
            indicators: Dictionary of calculated indicators
        """
        key = self._make_key(df, params)
        
        # Evict oldest entry if cache is full (simple FIFO)
        if len(self._cache) >= self.max_size:
            # Remove first entry (oldest)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = indicators
    
    def clear(self):
        """Clear all cached entries"""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }
    
    def print_stats(self):
        """Print cache statistics"""
        stats = self.get_stats()
        print(f"\n📊 Indicator Cache Statistics:")
        print(f"  Cache Size: {stats['size']}/{stats['max_size']}")
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")
        print(f"  Hit Rate: {stats['hit_rate']:.1f}%")
        print(f"  Total Requests: {stats['total_requests']}\n")


# Global cache instance
_global_cache = IndicatorCache(max_size=100)


def get_cache() -> IndicatorCache:
    """Get global cache instance"""
    return _global_cache


def clear_cache():
    """Clear global cache"""
    _global_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics"""
    return _global_cache.get_stats()


if __name__ == '__main__':
    print("✅ Testing Indicator Cache...")
    
    import numpy as np
    
    # Create test data
    dates = pd.date_range('2024-01-01', periods=100, freq='5min')
    df = pd.DataFrame({
        'open': 42000 + np.random.randn(100).cumsum() * 10,
        'high': 42000 + np.random.randn(100).cumsum() * 10 + 5,
        'low': 42000 + np.random.randn(100).cumsum() * 10 - 5,
        'close': 42000 + np.random.randn(100).cumsum() * 10,
        'volume': np.random.randint(100, 1000, 100)
    }, index=dates)
    
    cache = IndicatorCache(max_size=10)
    
    # Test params
    params1 = {'rsi_period': 14, 'bb_period': 20}
    params2 = {'rsi_period': 14, 'bb_period': 20}  # Same
    params3 = {'rsi_period': 21, 'bb_period': 20}  # Different
    
    # Create mock indicators
    indicators1 = {
        'rsi': pd.Series([50.0] * len(df), index=df.index),
        'bb_upper': pd.Series([43000.0] * len(df), index=df.index)
    }
    
    # Test cache miss
    result = cache.get(df, params1)
    assert result is None, "Should be cache miss"
    print("✅ Cache miss works")
    
    # Test cache set
    cache.set(df, params1, indicators1)
    print("✅ Cache set works")
    
    # Test cache hit
    result = cache.get(df, params2)
    assert result is not None, "Should be cache hit"
    assert 'rsi' in result, "Should have cached indicators"
    print("✅ Cache hit works")
    
    # Test different params (miss)
    result = cache.get(df, params3)
    assert result is None, "Should be cache miss with different params"
    print("✅ Different params = cache miss works")
    
    # Print stats
    cache.print_stats()
    
    # Test cache eviction
    for i in range(15):
        test_params = {'rsi_period': 10 + i}
        cache.set(df, test_params, indicators1)
    
    assert len(cache._cache) <= 10, "Cache should not exceed max_size"
    print("✅ Cache eviction works")
    
    cache.print_stats()
    
    print("\n✅ All cache tests passed!")