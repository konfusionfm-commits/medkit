from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

from medkit.cache import CacheBackend


class MemoryCache(CacheBackend):
    """
    In-memory Time-To-Live (TTL) cache.
    Thread-safe with bounded size eviction (LRU).
    """

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self._data: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._lock = threading.RLock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._data:
                self.misses += 1
                return None

            entry = self._data[key]
            if time.time() > entry["expires_at"]:
                del self._data[key]
                self.evictions += 1
                self.misses += 1
                return None

            # LRU bump
            value = self._data.pop(key)
            self._data[key] = value

            self.hits += 1
            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            if len(self._data) >= self.max_size and key not in self._data:
                # Evict oldest
                oldest_key = next(iter(self._data))
                del self._data[oldest_key]
                self.evictions += 1

            ttl = ttl or self.default_ttl
            self._data[key] = {"value": value, "expires_at": time.time() + ttl}

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "size": len(self._data),
                "max_size": self.max_size,
            }
