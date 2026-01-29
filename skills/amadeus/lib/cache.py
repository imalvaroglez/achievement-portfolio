"""
Simple in-memory cache for API responses.

Provides TTL-based caching to reduce API calls and improve response times.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional


class ResponseCache:
    """
    In-memory cache with TTL support.
    
    Thread-safe for basic operations. Cache is not persisted
    across process restarts (by design - no stale data).
    """
    
    def __init__(self, default_ttl: int = 900, max_entries: int = 1000):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default TTL in seconds (15 minutes)
            max_entries: Maximum cache entries (LRU eviction)
        """
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry, access_time)
    
    def make_key(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a cache key from endpoint and parameters.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Cache key string
        """
        key_data = {
            'endpoint': endpoint,
            'params': params or {},
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a cached value if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        value, expiry, _ = self._cache[key]
        
        if time.time() > expiry:
            del self._cache[key]
            return None
        
        # Update access time for LRU
        self._cache[key] = (value, expiry, time.time())
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Cache a value.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if not specified)
        """
        # Evict old entries if at capacity
        if len(self._cache) >= self.max_entries:
            self._evict_oldest()
        
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry, time.time())
    
    def _evict_oldest(self) -> None:
        """Evict the least recently accessed entry."""
        if not self._cache:
            return
        
        # Find oldest by access time
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][2])
        del self._cache[oldest_key]
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        valid_count = sum(1 for _, expiry, _ in self._cache.values() if now < expiry)
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_count,
            'expired_entries': len(self._cache) - valid_count,
            'max_entries': self.max_entries,
        }
