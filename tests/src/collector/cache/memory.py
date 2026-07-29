from __future__ import annotations

from datetime import timedelta
from typing import Any

from collector.cache.cache import Cache
from collector.core.logging import get_logger


class MemoryCache(Cache):
    def __init__(self):
        self.__logger = get_logger(__name__)
        self.__cache: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        value = self.__cache.get(key)
        self.__logger.info("cache.get", key=key, found=value is not None)
        return value
        
    def set(self, key: str, value: Any, ttl: timedelta | None = None) -> None:
        self.__cache[key] = value
        self.__logger.info("cache.set", key=key)
        
    def delete(self, key: str) -> None:
        self.__cache.pop(key, None)
        self.__logger.info("cache.delete", key=key)
    
    def clear(self) -> None:
        self.__cache.clear()
        self.__logger.info("cache.clear")
            