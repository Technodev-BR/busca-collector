from __future__ import annotations

from collector.cache.cache import Cache
from collector.core.settings import Settings
from collector.http.http import Http
from collector.sources.caixa.analysis import CaixaAnalysis
from collector.sources.caixa.enricher import CaixaEnricher
from collector.sources.caixa.parser import CaixaParser
from collector.sources.caixa.source import CaixaSource
from collector.sources.source import Source
from collector.storage.storage import Storage


def configure_source(
    settings: Settings,
    http: Http,
    storage: Storage,
    cache: Cache,
) -> Source:
    return CaixaSource(
        http=http,
        storage=storage,
        settings=settings,
        parser=CaixaParser(),
        enricher=CaixaEnricher(settings, http, cache),
        analysis=CaixaAnalysis(),
    )


__all__ = ["CaixaSource", "configure_source"]
