from __future__ import annotations

import shutil
from pathlib import Path

from collector.core.enums import StorageDirectory
from collector.core.logging import get_logger
from collector.storage.models import StorageFile
from collector.storage.storage import Storage


class LocalStorage(Storage):
    
    def __init__(self, root_path: str ):
        self.__root = Path(root_path)
        self.__logger = get_logger(__name__)
    
    def save(self, directory: StorageDirectory, files: list[StorageFile]) -> None:
        if not files:
            self.__logger.warning("storage.save.no_files", directory=directory)
            return
        
        folder = self.__root / directory
        self.__logger.info("storage.save.start", directory=str(folder), files=len(files))
        
        if folder.exists():
            shutil.rmtree(folder)
            self.__logger.info(
                "storage.save.directory_cleaned", directory=str(folder), files=len(files)
            )
            
        folder.mkdir(
            parents=True,
            exist_ok=True
        )
         
        for file in files:
            path = folder / file.name
            path.write_bytes(file.content)  
            self.__logger.info("storage.save.file_saved", file=file.name)
                               
        self.__logger.info("storage.save.finished", directory=str(folder), files=len(files))
                        
    def read(self, directory: StorageDirectory) -> list[StorageFile]:
        folder = self.__root / directory
        
        if not folder.exists():
            self.__logger.info("storage.read.directory_empty", directory=str(folder))
            return []
        
        paths = [path for path in folder.iterdir() if path.is_file()]
        
        if not paths:
            self.__logger.info("storage.read.directory_empty", directory=str(folder))
            return []
        
        files = []
        
        for path in sorted(paths):
            files.append(
                StorageFile(
                    name=path.name,
                    content=path.read_bytes()
                )
            )
        
        self.__logger.info("storage.read.sucess", directory=str(folder), files=len(files))
        return files
        
        