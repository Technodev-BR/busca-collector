from __future__ import annotations

from abc import ABC, abstractmethod

from collector.core.enums import StorageDirectory
from collector.storage.models import StorageFile


class Storage(ABC):
    
    @abstractmethod
    def save(self, directory: StorageDirectory, files: list[StorageFile]) -> None:
        """ salva os arquivo no diretorio/bucket, se caso ja existerem substituem"""
        pass
        
    @abstractmethod
    def read(self, directory: StorageDirectory) -> list[StorageFile]:
        """ retorna todos os arquivos do diretorio/bucket"""
        pass