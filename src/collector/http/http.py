from __future__ import annotations

from abc import ABC, abstractmethod

from collector.http.models import HttpResponse


class Http(ABC):

    @abstractmethod
    def get(self, url: str, **kwargs) -> HttpResponse:
        """Executa uma requisição GET."""
        ...

    @abstractmethod
    def post(self, url: str, **kwargs) -> HttpResponse:
        """Executa uma requisição POST."""
        ...
