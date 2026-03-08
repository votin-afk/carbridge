"""Caching utilities"""
from datetime import datetime, timedelta
from typing import Any, Optional

# Simple in-memory cache
_cache = {}
_cache_ttl = {}
DEFAULT_TTL = 300  # 5 minutes

def get_cached(key: str) -> Optional[Any]:
    """Get item from cache if not expired"""
    if key in _cache:
        if datetime.now() < _cache_ttl.get(key, datetime.min):
            return _cache[key]
        else:
            # Expired, remove from cache
            del _cache[key]
            del _cache_ttl[key]
    return None

def set_cache(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Set item in cache with TTL"""
    _cache[key] = value
    _cache_ttl[key] = datetime.now() + timedelta(seconds=ttl)

def clear_cache(key: Optional[str] = None) -> None:
    """Clear cache - specific key or all"""
    global _cache, _cache_ttl
    if key:
        _cache.pop(key, None)
        _cache_ttl.pop(key, None)
    else:
        _cache = {}
        _cache_ttl = {}
