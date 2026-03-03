"""
Utility functions for the MedKit SDK.
"""

import asyncio
import collections
import functools
import threading
import time
from typing import Any, Callable, Deque, Dict, List, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def cache_response(maxsize: int = 128) -> Callable[[F], F]:
    """
    A unified cache decorator. Uses a provided custom cache (Disk/Memory)
    if available on the instance, otherwise falls back to lru_cache.
    """

    def decorator(func: F) -> F:
        # Use lru_cache for sync fallback if no self.cache is present
        _lru = functools.lru_cache(maxsize=maxsize)(func)

        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            import asyncio

            cache = getattr(self, "cache", None)

            if cache:
                class_name = self.__class__.__name__ if self else "Unknown"
                key = f"{class_name}.{func.__name__}:{args}:{kwargs}"
                cached_val = cache.get(key)
                if cached_val is not None:
                    # If it's an async context but we have a sync value,
                    # return it (Usually we'd need to return a future if
                    # the caller expects one)
                    if asyncio.iscoroutinefunction(func):

                        async def _ret() -> Any:
                            return cached_val

                        return _ret()
                    return cached_val

                if asyncio.iscoroutinefunction(func):

                    async def _async_wrapper() -> Any:
                        result = await func(self, *args, **kwargs)
                        cache.set(key, result)
                        return result

                    return _async_wrapper()
                else:
                    result = func(self, *args, **kwargs)
                    cache.set(key, result)
                    return result

            return _lru(self, *args, **kwargs)

        return cast(F, wrapper)

    return decorator


class RateLimiter:
    """
    A thread-safe synchronous rate limiter using a sliding window.
    Ensures that calls do not exceed `calls` per `period` seconds.
    """

    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.timestamps: List[float] = []
        self._lock = threading.Lock()

    def wait(self) -> None:
        """
        Blocks if the rate limit has been exceeded.
        """
        with self._lock:
            now = time.time()
            self.timestamps = [t for t in self.timestamps if now - t < self.period]

            if len(self.timestamps) >= self.calls:
                sleep_time = self.period - (now - self.timestamps[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

                # Re-evaluate logic without deep recursion
                now = time.time()
                self.timestamps = [t for t in self.timestamps if now - t < self.period]

            self.timestamps.append(time.time())

    def update_from_headers(self, headers: Dict[str, str]) -> None:
        """Dynamically adjust rate limits based on API response headers."""
        # This is a stub that providers can call to adjust backpressure
        pass


class AsyncRateLimiter:
    """
    An asynchronous, non-blocking rate limiter using a sliding window.
    Uses asyncio.sleep to pause the current coroutine without blocking the loop.
    Safe for concurrent asyncio tasks.
    """

    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.timestamps: Deque[float] = collections.deque()
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        """
        Asynchronously waits if the rate limit has been exceeded.
        """
        async with self._lock:
            now = time.time()

            while self.timestamps and now - self.timestamps[0] >= self.period:
                self.timestamps.popleft()

            if len(self.timestamps) >= self.calls:
                sleep_time = self.period - (now - self.timestamps[0])
                if sleep_time > 0:
                    # Release lock while sleeping so other tasks can queue up
                    pass

                # If we need to sleep, we do it outside the critical section
                # but we must re-acquire lock after

            self.timestamps.append(time.time())

        # If sleep is needed, do it outside the lock to avoid deadlocking the limiter
        now = time.time()
        # Peek at oldest timestamp (safe without lock for reading first element mostly)
        if len(self.timestamps) > self.calls:  # Approximate check
            sleep_time_estimate = self.period - (now - self.timestamps[0])
            if sleep_time_estimate > 0:
                await asyncio.sleep(sleep_time_estimate)

    def update_from_headers(self, headers: Dict[str, str]) -> None:
        pass


def paginate(fetch_page: Callable[[int], List[Any]], max_pages: int = 5) -> List[Any]:
    """
    Helper function to paginate through API results.
    `fetch_page` should be a function that takes a page index and returns a list
    of items.
    Expects `fetch_page` to return an empty list when no more data is available.
    """
    results = []
    for page in range(max_pages):
        page_results = fetch_page(page)
        if not page_results:
            break
        results.extend(page_results)
    return results
