from __future__ import annotations

from typing import Any

from collector.core.enums import StorageDirectory
from collector.core.logging import get_logger
from collector.storage.models import StorageFile
from collector.storage.storage import Storage


class S3Storage(Storage):
    def __init__(self, client: Any, bucket: str):
        self.__client = client
        self.__bucket = bucket
        self.__logger = get_logger(__name__)

    def save(self, directory: StorageDirectory, files: list[StorageFile]) -> None:
        if not files:
            self.__logger.warning("storage.save.no_files", directory=directory)
            return

        prefix = f"{directory}/"
        self.__logger.info("storage.save.start", directory=prefix, files=len(files))

        paginator = self.__client.get_paginator("list_objects_v2")
        antigas = [
            obj["Key"]
            for pagina in paginator.paginate(Bucket=self.__bucket, Prefix=prefix)
            for obj in pagina.get("Contents", [])
        ]
        if antigas:
            self.__client.delete_objects(
                Bucket=self.__bucket,
                Delete={"Objects": [{"Key": chave} for chave in antigas]},
            )
            self.__logger.info(
                "storage.save.directory_cleaned", directory=prefix, files=len(antigas)
            )

        for file in files:
            self.__client.put_object(
                Bucket=self.__bucket,
                Key=f"{prefix}{file.name}",
                Body=file.content,
            )
            self.__logger.info("storage.save.file_saved", file=file.name)

        self.__logger.info("storage.save.finished", directory=prefix, files=len(files))

    def read(self, directory: StorageDirectory) -> list[StorageFile]:
        prefix = f"{directory}/"
        paginator = self.__client.get_paginator("list_objects_v2")
        keys = [
            obj["Key"]
            for pagina in paginator.paginate(Bucket=self.__bucket, Prefix=prefix)
            for obj in pagina.get("Contents", [])
            if not obj["Key"].endswith("/")
        ]

        if not keys:
            self.__logger.info("storage.read.directory_empty", directory=prefix)
            return []

        files: list[StorageFile] = []
        for key in sorted(keys):
            obj = self.__client.get_object(Bucket=self.__bucket, Key=key)
            files.append(StorageFile(name=key[len(prefix):], content=obj["Body"].read()))

        self.__logger.info("storage.read.sucess", directory=prefix, files=len(files))
        return files
