from __future__ import annotations

from collector.fontes.caixa.mapper import mapear, parse_descricao
from collector.fontes.caixa.parser import parsear_csv, resolver_colunas


def _primeiro_imovel(csv_bytes):
    _, registros = parsear_csv(csv_bytes)
    colunas = resolver_colunas(list(registros[0].keys()))
    return mapear(registros[0], colunas, "SP")


def test_mapear_campos_basicos(csv_bytes):
    imovel = _primeiro_imovel(csv_bytes)
    assert imovel is not None
    assert imovel.codigo == "1444408501866"
    assert imovel.uf == "SP"
    assert imovel.cidade == "ADAMANTINA"
    assert imovel.preco == 501000.00
    assert imovel.valor_avaliacao == 600000.00
    assert imovel.desconto_pct == 16.5
    assert imovel.financiamento is False
    assert imovel.modalidade == "Leilão SFI - Edital único"


def test_serializacao_camelcase(csv_bytes):
    imovel = _primeiro_imovel(csv_bytes)
    data = imovel.model_dump(by_alias=True, mode="json")
    # A API Java espera camelCase.
    assert "valorAvaliacao" in data
    assert "descontoPct" in data
    assert data["valorAvaliacao"] == 600000.00
    assert "valor_avaliacao" not in data


def test_financiamento_sim(csv_bytes):
    _, registros = parsear_csv(csv_bytes)
    colunas = resolver_colunas(list(registros[0].keys()))
    imovel = mapear(registros[1], colunas, "SP")
    assert imovel is not None
    assert imovel.financiamento is True
    assert imovel.cidade == "SANTOS"


def test_parse_descricao_extrai_tipo_e_areas():
    d = parse_descricao(
        "Casa, 0.00 de área total, 171.43 de área privativa, 384.00 de área do terreno."
    )
    assert d["tipo"] == "Casa"
    assert d["area_privativa"] == 171.43
    assert d["area_terreno"] == 384.00


def test_mapear_sem_codigo_retorna_none():
    colunas = {"codigo": "N° do imóvel"}
    assert mapear({"N° do imóvel": ""}, colunas, "SP") is None
