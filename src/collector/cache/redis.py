from __future__ import annotations

from datetime import timedelta
from typing import Any

from redis import Redis

from collector.cache.cache import Cache
from collector.core.logging import get_logger


class RedisCache(Cache):
    def __init__(self, client: Redis):
        self.__logger = get_logger(__name__)
        self.__client = client

    def get(self, key: str) -> Any | None:
        self.__logger.info("redis.get", key=key)
        return self.__client.get(key)

    def set(self, key: str, value: Any, ttl: timedelta | None = None) -> None:
        if ttl:
            self.__client.set(key, value, ex=ttl)
        else:
            self.__client.set(key, value)
        self.__logger.info("redis.set", key=key)

    def delete(self, key: str) -> None:
        self.__client.delete(key)
        self.__logger.info("redis.delete", key=key)

    def clear(self) -> None:
        self.__client.flushdb()
        self.__logger.info("redis.clear")
