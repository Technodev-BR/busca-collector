from __future__ import annotations

from datetime import date

import pytest

from collector.fontes.caixa.parser import (
    brl_para_float,
    extrair_data_geracao,
    parsear_csv,
    resolver_colunas,
)


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("501.000,00", 501000.00),
        ("1.234.567,89", 1234567.89),
        ("0.00", 0.0),
        ("16,50", 16.5),
        ("  250.000,00 ", 250000.00),
        ("", None),
        (None, None),
        ("abc", None),
    ],
)
def test_brl_para_float(entrada, esperado):
    assert brl_para_float(entrada) == esperado


def test_parsear_csv_pula_duas_linhas_e_le_cabecalho(csv_bytes):
    gerado_em, registros = parsear_csv(csv_bytes)
    assert gerado_em == date(2026, 7, 15)
    assert len(registros) == 2
    assert registros[0]["UF"] == "SP"
    assert registros[0]["Cidade"] == "ADAMANTINA"
    # trim aplicado (código vinha com espaço à direita)
    assert registros[0]["N° do imóvel"] == "1444408501866"


def test_resolver_colunas(csv_bytes):
    _, registros = parsear_csv(csv_bytes)
    colunas = resolver_colunas(list(registros[0].keys()))
    assert colunas["codigo"] == "N° do imóvel"
    assert colunas["preco"] == "Preço"
    assert colunas["avaliacao"] == "Valor de avaliação"
    assert colunas["modalidade"] == "Modalidade de venda"
    assert colunas["link"] == "Link de acesso"


def test_extrair_data_geracao():
    assert extrair_data_geracao(["foo;Data de geração;01/02/2026", ""]) == date(2026, 2, 1)
    assert extrair_data_geracao(["sem data", ""]) is None


def test_parsear_csv_curto_falha():
    with pytest.raises(ValueError):
        parsear_csv(b"linha1\nlinha2\n")
