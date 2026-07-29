from __future__ import annotations

from collector.api.api import Api
from collector.api.client import ApiClient
from collector.api.models import ApiRecord
from collector.core.settings import Settings
from collector.http.http import Http


def configure_api(settings: Settings, http: Http) -> Api:
    return ApiClient(settings, http)


__all__ = ["Api", "ApiClient", "ApiRecord", "configure_api"]
