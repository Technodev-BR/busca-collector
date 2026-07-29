from __future__ import annotations

from datetime import timedelta

import fakeredis

from collector.cache import configure_cache
from collector.cache.memory import MemoryCache
from collector.cache.redis import RedisCache


def test_memory_set_get():
    cache = MemoryCache()
    assert cache.get("k") is None
    cache.set("k", "v")
    assert cache.get("k") == "v"


def test_memory_delete_e_clear():
    cache = MemoryCache()
    cache.set("a", "1")
    cache.set("b", "2")
    cache.delete("a")
    assert cache.get("a") is None
    assert cache.get("b") == "2"
    cache.clear()
    assert cache.get("b") is None


def test_configure_cache_memory_quando_redis_desabilitado(settings):
    cache = configure_cache(settings)
    assert isinstance(cache, MemoryCache)


def test_redis_cache_set_get():
    fake = fakeredis.FakeRedis(decode_responses=True)
    cache = RedisCache(fake)
    cache.set("caixa:detail:SP:111", "fp1", ttl=timedelta(days=1))
    assert cache.get("caixa:detail:SP:111") == "fp1"


def test_redis_cache_delete_e_clear():
    fake = fakeredis.FakeRedis(decode_responses=True)
    cache = RedisCache(fake)
    cache.set("k", "v")
    cache.delete("k")
    assert cache.get("k") is None
    cache.set("k2", "v2")
    cache.clear()
    assert cache.get("k2") is None
