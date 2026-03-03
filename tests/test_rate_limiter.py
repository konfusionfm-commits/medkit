import time

import pytest

from medkit.utils import AsyncRateLimiter, RateLimiter


def test_sync_rate_limiter():
    limiter = RateLimiter(calls=3, period=0.5)

    start = time.time()
    for _ in range(3):
        limiter.wait()
    # First 3 should be immediate
    assert time.time() - start < 0.1

    # 4th should block for ~0.5s
    limiter.wait()
    assert time.time() - start >= 0.4


@pytest.mark.asyncio
async def test_async_rate_limiter():
    limiter = AsyncRateLimiter(calls=3, period=0.5)

    start = time.time()
    for _ in range(3):
        await limiter.wait()
    # First 3 should be immediate
    assert time.time() - start < 0.1

    # 4th should block for ~0.5s
    await limiter.wait()
    assert time.time() - start >= 0.4
