from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class CacheBackend(Protocol):
    """Protocol defining the interface all cache backends must implement."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in the cache with an optional TTL."""
        ...

    def clear(self) -> None:
        """Clear all entries from the cache."""
        ...

    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        ...
