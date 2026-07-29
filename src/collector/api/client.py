from __future__ import annotations

from collector.api.api import Api
from collector.api.models import ApiRecord
from collector.core.exceptions import (
    ApiUnauthorizedException,
    ApiUnavailableException,
    ApiValidationException,
)
from collector.core.logging import get_logger
from collector.core.settings import Settings
from collector.http.http import Http


class ApiClient(Api):
    def __init__(self, settings: Settings, http: Http) -> None:
        self.__logger = get_logger(__name__)
        self.__endpoint = settings.backend_base_url
        self.__http = http
        self.__headers = {
            "X-Internal-Token": settings.internal_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def ingest_batch(self, records: list[ApiRecord]) -> None:
        self.__logger.info("api.ingest", records=len(records))
        for record in records:
            self.__logger.info("api.ingest.payload", key=str(record.key), payload=record.payload)
        for record in records:
            self.ingest(record)

    def ingest(self, record: ApiRecord) -> None:
        response = self.__http.post(
            url=self.__endpoint,
            headers={**self.__headers, "Idempotency-Key": str(record.key)},
            json=record.payload,
        )
        self.__validate_response(response)

    @staticmethod
    def __validate_response(response) -> None:
        if response.status_code == 400:
            raise ApiValidationException()
        if response.status_code == 401:
            raise ApiUnauthorizedException()
        if response.status_code == 500:
            raise ApiUnavailableException()
