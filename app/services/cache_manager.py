"""
Cache manager với TTL và invalidation support.
Tối ưu performance bằng cách cache computed metrics.
"""

from functools import lru_cache, wraps
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
import hashlib
import json


class TTLCache:
    """Simple TTL-based cache."""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Args:
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        # Check if expired
        if datetime.now() > self._timestamps[key]:
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        self._cache[key] = value
        self._timestamps[key] = datetime.now() + timedelta(seconds=ttl)
    
    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._timestamps.clear()
    
    def invalidate(self, key: str):
        """Invalidate specific key."""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]


# Global cache instance
_cache = TTLCache(default_ttl=3600)  # 1 hour default


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl: int = 3600):
    """
    Decorator để cache function results với TTL.
    
    Usage:
        @cached(ttl=1800)  # 30 minutes
        def expensive_function(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = _cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Compute and cache
            result = func(*args, **kwargs)
            _cache.set(key, result, ttl=ttl)
            return result
        
        wrapper.cache_clear = lambda: _cache.clear()
        wrapper.cache_invalidate = lambda k: _cache.invalidate(k)
        return wrapper
    return decorator


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        'size': len(_cache._cache),
        'keys': list(_cache._cache.keys())
    }


def clear_cache():
    """Clear all cache."""
    _cache.clear()


def invalidate_cache_pattern(pattern: str):
    """Invalidate cache keys matching pattern."""
    keys_to_remove = [k for k in _cache._cache.keys() if pattern in k]
    for key in keys_to_remove:
        _cache.invalidate(key)

