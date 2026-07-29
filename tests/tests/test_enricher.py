from __future__ import annotations

from pathlib import Path

from collector.cache.memory import MemoryCache
from collector.http.http import Http
from collector.http.models import HttpResponse
from collector.sources.caixa.enricher import CaixaEnricher
from collector.sources.caixa.models import AuctionRecord, CaixaItem

FIXTURES = Path(__file__).parent / "fixtures"
_HTML = (FIXTURES / "detalhe_8787713989126.html").read_bytes()


class _FakeHttp(Http):
    def __init__(self, content: bytes = _HTML, status: int = 200) -> None:
        self.content = content
        self.status = status
        self.get_calls = 0

    def get(self, url: str, **kwargs) -> HttpResponse:
        self.get_calls += 1
        return HttpResponse(status_code=self.status, url=url, headers={}, content=self.content)

    def post(self, url: str, **kwargs) -> HttpResponse:  # pragma: no cover - n?o usado
        raise NotImplementedError


def _item(code: str = "8787713989126") -> CaixaItem:
    return CaixaItem(
        code=code,
        state="SP",
        city="Altin?polis",
        modality="Leil?o",
        link="https://example.com",
    )


def test_enricher_busca_detalhe_e_preenche(settings):
    http = _FakeHttp()
    records = [AuctionRecord(item=_item())]
    CaixaEnricher(settings, http, MemoryCache()).process(records)

    assert http.get_calls == 1
    assert records[0].detail is not None
    assert records[0].detail.property_type == "Casa"


def test_enricher_pula_quando_fingerprint_no_cache(settings):
    http = _FakeHttp()
    cache = MemoryCache()
    enricher = CaixaEnricher(settings, http, cache)

    records = [AuctionRecord(item=_item())]
    enricher.process(records)
    assert http.get_calls == 1

    # 2? passada: mesmo fingerprint j? registrado no cache -> n?o rebusca.
    enricher.process([AuctionRecord(item=_item())])
    assert http.get_calls == 1


def test_enricher_respeita_detalhar_inline_false(settings):
    cfg = settings.model_copy(update={"detalhar_inline": False})
    http = _FakeHttp()
    records = [AuctionRecord(item=_item())]
    CaixaEnricher(cfg, http, MemoryCache()).process(records)

    assert http.get_calls == 0
    assert records[0].detail is None


def test_enricher_respeita_limite(settings):
    cfg = settings.model_copy(update={"detalhe_limite": 1})
    http = _FakeHttp()
    records = [AuctionRecord(item=_item("1")), AuctionRecord(item=_item("2"))]
    CaixaEnricher(cfg, http, MemoryCache()).process(records)

    assert http.get_calls == 1
