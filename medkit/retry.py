from __future__ import annotations

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from medkit.config import RetryConfig

logger = logging.getLogger("medkit.retry")

T = TypeVar("T")


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate the backoff delay including jitter."""
    # Exponential backoff: base_delay * 2^attempt
    delay: float = min(float(config.base_delay) * (2**attempt), float(config.max_delay))

    if config.jitter == "none":
        return delay
    elif config.jitter == "full":
        return random.uniform(0, delay)
    elif config.jitter == "equal":
        temp = delay / 2
        return temp + random.uniform(0, temp)
    elif config.jitter == "decorrelated":
        # Decorrelated jitter requires knowing the previous delay,
        # but for simplicity in a stateless function, we approximate
        # by providing a random value between base_delay and current exponential delay
        return random.uniform(float(config.base_delay), delay)

    return delay


def retry(
    config: RetryConfig,
    provider_name: str = "unknown",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for adding exponential backoff and retry logic to functions.
    Supports both synchronous and asynchronous functions.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                attempt = 0
                while True:
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if not isinstance(e, config.retry_on) or attempt >= config.max_retries:
                            raise

                        # Respect Retry-After headers if present
                        delay = getattr(e, "retry_after", None)
                        if delay is None:
                            delay = _calculate_delay(attempt, config)

                        logger.warning(
                            f"Request failed for {provider_name} "
                            f"(attempt {attempt + 1}/{config.max_retries + 1}). "
                            f"Retrying in {delay:.2f}s. Error: {str(e)}"
                        )
                        await asyncio.sleep(delay)
                        attempt += 1

            return async_wrapper

        else:

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                attempt = 0
                while True:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if not isinstance(e, config.retry_on) or attempt >= config.max_retries:
                            raise

                        delay = getattr(e, "retry_after", None)
                        if delay is None:
                            delay = _calculate_delay(attempt, config)

                        logger.warning(
                            f"Request failed for {provider_name} "
                            f"(attempt {attempt + 1}/{config.max_retries + 1}). "
                            f"Retrying in {delay:.2f}s. Error: {str(e)}"
                        )
                        time.sleep(delay)
                        attempt += 1

            return sync_wrapper

    return decorator
