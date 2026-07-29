from __future__ import annotations

from collector.api.api import Api
from collector.api.models import ApiRecord
from collector.core.logging import get_logger
from collector.core.settings import Settings
from collector.sources.source import Source


class Pipeline:
    def __init__(self, settings: Settings, source: Source, api: Api) -> None:
        self.__logger = get_logger(__name__)
        self.__settings = settings
        self.__source = source
        self.__api = api

    def run(self) -> None:
        self.__logger.info("pipeline.start", fonte=self.__settings.fonte)

        records = self.__source.collect()
        api_records = [
            ApiRecord(
                key=f"{self.__settings.fonte}:{record.item.state}:{record.item.code}",
                payload=record.model_dump(by_alias=True, mode="json"),
            )
            for record in records
        ]

        self.__api.ingest_batch(api_records)
        self.__logger.info("pipeline.finished", records=len(api_records))
