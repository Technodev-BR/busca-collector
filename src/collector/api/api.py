from __future__ import annotations

from abc import ABC, abstractmethod

from collector.api.models import ApiRecord


class Api(ABC):
    
    @abstractmethod
    def ingest(self,record: ApiRecord) -> None:
        """ Envia um unico registro """
        pass
        
    @abstractmethod
    def ingest_batch(self,record: list[ApiRecord]) -> None:
        """ Envia um lote de registro  """
        pass
        