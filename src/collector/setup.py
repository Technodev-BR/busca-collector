from __future__ import annotations

from collector.api import configure_api
from collector.cache import configure_cache
from collector.core.logging import configure_logging
from collector.core.settings import configure_settings
from collector.http import configure_http
from collector.pipeline import Pipeline
from collector.sources.caixa import configure_source
from collector.storage import configure_storage


def setup() -> Pipeline:
    settings = configure_settings()
    configure_logging(
        level=settings.log_level,
        json_logs=settings.json_logs,
        log_dir=settings.log_dir,
        retention_days=settings.log_retention_days,
    )

    http = configure_http(settings)
    storage = configure_storage(settings)
    cache = configure_cache(settings)

    api = configure_api(settings, http)
    source = configure_source(settings, http, storage, cache)

    return Pipeline(settings, source, api)
