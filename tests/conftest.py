from typing import Iterator

import httpx
import pytest

from medkit.cache_backends import MemoryCache
from medkit.config import MedKitConfig


@pytest.fixture
def test_config() -> MedKitConfig:
    return MedKitConfig(timeout=1.0, max_connections=10, cache_backend="none", log_level="CRITICAL")


@pytest.fixture
def memory_cache() -> MemoryCache:
    return MemoryCache(default_ttl=60, max_size=10)


@pytest.fixture
def mock_httpx_client() -> Iterator[httpx.Client]:
    # Need to integrate pytest-httpx or respx here
    yield httpx.Client()


@pytest.fixture
def mock_httpx_async_client() -> Iterator[httpx.AsyncClient]:
    yield httpx.AsyncClient()
