from __future__ import annotations

from collector.cache.cache import Cache
from collector.cache.memory import MemoryCache
from collector.core.logging import get_logger
from collector.core.settings import Settings

log = get_logger(__name__)


def configure_cache(settings: Settings) -> Cache:
    if not settings.redis_enabled:
        return MemoryCache()
    try:
        from redis import Redis

        from collector.cache.redis import RedisCache

        return RedisCache(Redis.from_url(settings.redis_url))
    except Exception as ex:  # noqa: BLE001 - degradação graciosa se o Redis estiver fora
        log.warning("redis.indisponivel", error=str(ex))
        return MemoryCache()


__all__ = ["Cache", "MemoryCache", "configure_cache"]
