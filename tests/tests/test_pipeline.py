from __future__ import annotations

from collector.api.api import Api
from collector.api.models import ApiRecord
from collector.pipeline import Pipeline
from collector.sources.caixa.models import AuctionRecord, CaixaItem
from collector.sources.source import Source


class _FakeSource(Source):
    def __init__(self, records: list[AuctionRecord]) -> None:
        self.__records = records

    def collect(self) -> list[AuctionRecord]:
        return self.__records


class _FakeApi(Api):
    def __init__(self) -> None:
        self.batch: list[ApiRecord] = []

    def ingest(self, record: ApiRecord) -> None:  # pragma: no cover - não usado no pipeline
        self.batch.append(record)

    def ingest_batch(self, record: list[ApiRecord]) -> None:
        self.batch = record


def _item(code: str, state: str = "SP") -> CaixaItem:
    return CaixaItem(
        code=code,
        state=state,
        city="Santos",
        modality="Leilão",
        link="https://example.com",
    )


def test_pipeline_monta_e_envia_lote(settings):
    records = [
        AuctionRecord(item=_item("111")),
        AuctionRecord(item=_item("222", state="RJ")),
    ]
    api = _FakeApi()
    Pipeline(settings, _FakeSource(records), api).run()

    assert len(api.batch) == 2
    chaves = {r.key for r in api.batch}
    assert "caixa:SP:111" in chaves
    assert "caixa:RJ:222" in chaves


def test_pipeline_payload_em_camelcase(settings):
    api = _FakeApi()
    Pipeline(settings, _FakeSource([AuctionRecord(item=_item("111"))]), api).run()

    payload = api.batch[0].payload
    assert "item" in payload
    assert payload["item"]["code"] == "111"


def test_pipeline_lista_vazia(settings):
    api = _FakeApi()
    Pipeline(settings, _FakeSource([]), api).run()
    assert api.batch == []
