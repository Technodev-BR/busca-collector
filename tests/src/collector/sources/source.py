from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collector.sources.caixa.models import AuctionRecord


class Source(ABC):

    @abstractmethod
    def collect(self) -> list[AuctionRecord]:
        """Executa toda a coleta da fonte."""
        ...
