from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any


class Cache(ABC):
    
    @abstractmethod
    def get(self,key: str) -> Any | None:
        """ """
        pass
        
    @abstractmethod
    def set(self, key: str, value: Any, ttl: timedelta | None = None) -> None:
        """ """
        pass
        
    @abstractmethod
    def delete(self, key: str) -> None:
        """ """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """ """
        pass