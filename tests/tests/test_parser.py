from __future__ import annotations

from collector.sources.caixa.models import AuctionRecord
from collector.sources.caixa.parser import CaixaParser
from collector.storage.models import StorageFile


def _records(csv_bytes: bytes) -> list[AuctionRecord]:
    files = [StorageFile(name="SP.csv", content=csv_bytes)]
    return CaixaParser().parse(files)


def test_parse_le_dois_imoveis(csv_bytes):
    records = _records(csv_bytes)
    assert len(records) == 2
    assert all(isinstance(r, AuctionRecord) for r in records)


def test_mapear_campos_basicos(csv_bytes):
    item = _records(csv_bytes)[0].item
    assert item.code == "1444408501866"
    assert item.state == "SP"
    assert item.city == "ADAMANTINA"
    assert item.price == 501000.00
    assert item.appraisal_value == 600000.00
    assert item.discount_pct == 16.5
    assert item.financing is False
    assert item.modality == "Leilão SFI - Edital único"


def test_financiamento_sim(csv_bytes):
    item = _records(csv_bytes)[1].item
    assert item.financing is True
    assert item.city == "SANTOS"


def test_serializacao_camelcase(csv_bytes):
    item = _records(csv_bytes)[0].item
    data = item.model_dump(by_alias=True, mode="json")
    # A API espera camelCase.
    assert "appraisalValue" in data
    assert "discountPct" in data
    assert data["appraisalValue"] == 600000.00
    assert "appraisal_value" not in data


def test_uf_derivada_do_nome_do_arquivo(csv_bytes):
    files = [StorageFile(name="rj.csv", content=csv_bytes)]
    records = CaixaParser().parse(files)
    # A UF do CSV ("SP") tem prioridade sobre a do nome do arquivo quando presente.
    assert records[0].item.state == "SP"


def test_csv_sem_cabecalho_retorna_vazio():
    lixo = b"linha1\nlinha2\nlinha3\n"
    records = CaixaParser().parse([StorageFile(name="SP.csv", content=lixo)])
    assert records == []
