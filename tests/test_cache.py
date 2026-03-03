import time

from medkit.cache_backends.disk import DiskCache
from medkit.cache_backends.memory import MemoryCache


def test_memory_cache_basic_ops():
    cache = MemoryCache(default_ttl=60, max_size=2)

    # Test Set/Get
    cache.set("a", 1)
    assert cache.get("a") == 1

    # Test Size limit (LRU Eviction)
    cache.set("b", 2)
    cache.set("c", 3)

    # "a" should be evicted
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3

    stats = cache.get_stats()
    assert stats["size"] == 2
    assert stats["evictions"] == 1


def test_memory_cache_ttl():
    cache = MemoryCache(default_ttl=1, max_size=10)
    cache.set("key", "val", ttl=0.1)

    assert cache.get("key") == "val"
    time.sleep(0.2)
    assert cache.get("key") is None


def test_disk_cache_basic_ops(tmp_path):
    cache_dir = str(tmp_path / "cache")
    cache = DiskCache(cache_dir=cache_dir, default_ttl=60)

    cache.set("test_key", {"data": 123})
    assert cache.get("test_key") == {"data": 123}

    cache.clear()
    assert cache.get("test_key") is None

    stats = cache.get_stats()
    assert stats["files_count"] == 0
