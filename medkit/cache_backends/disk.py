from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel

from medkit.cache import CacheBackend


class DiskCache(CacheBackend):
    """
    Persistent JSON-based cache for medical data.
    Thread-safe access to disk.
    """

    def __init__(self, cache_dir: str = ".medkit_cache", default_ttl: int = 3600):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self._lock = threading.RLock()

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        self.hits = 0
        self.misses = 0

    def _get_path(self, key: str) -> str:
        # Simple hash-based filename to avoid illegal characters in keys
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            path = self._get_path(key)
            if not os.path.exists(path):
                self.misses += 1
                return None

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if time.time() > data.get("expires_at", 0):
                    os.remove(path)
                    self.misses += 1
                    return None

                self.hits += 1
                return data["value"]
            except (json.JSONDecodeError, KeyError, OSError):
                self.misses += 1
                return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            path = self._get_path(key)

            # Handle Pydantic models by converting to dict
            if isinstance(value, BaseModel):
                value_to_store = value.model_dump()
            else:
                value_to_store = value

            ttl = ttl or self.default_ttl

            data = {
                "value": value_to_store,
                "expires_at": time.time() + ttl,
                "key": key,  # For debugging
            }

            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except OSError:
                pass

    def clear(self) -> None:
        with self._lock:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception:
                    pass
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            count = 0
            size_bytes = 0
            if os.path.exists(self.cache_dir):
                for f in os.listdir(self.cache_dir):
                    fp = os.path.join(self.cache_dir, f)
                    if os.path.isfile(fp):
                        count += 1
                        size_bytes += os.path.getsize(fp)
            return {
                "hits": self.hits,
                "misses": self.misses,
                "files_count": count,
                "size_bytes": size_bytes,
            }
