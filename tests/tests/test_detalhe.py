from __future__ import annotations

from pathlib import Path

import pytest

from collector.core.exceptions import FonteIndisponivelError, LayoutInesperadoError
from collector.sources.caixa.parser import CaixaDetailParser

FIXTURES = Path(__file__).parent / "fixtures"


def _html(nome: str) -> str:
    return (FIXTURES / nome).read_text(encoding="utf-8")


def _detail():
    return CaixaDetailParser().parse(_html("detalhe_8787713989126.html"), "8787713989126")


def test_parse_caracteristicas():
    d = _detail()
    assert d.property_type == "Casa"
    assert d.bedrooms == 2
    assert d.total_area == 47.75
    assert d.private_area == 47.75
    assert d.land_area == 140.00


def test_parse_valores_e_documentacao():
    d = _detail()
    assert d.minimum_sale_value == 86063.06
    assert d.first_auction_value == 86063.06
    assert d.registration == "15268"
    assert d.judicial_district == "ALTINOPOLIS-SP"
    assert d.registry_office == "01"
    assert d.municipal_registration == "0088490"
    assert d.notice == "0024/0326 - CPVE/RE"
    assert d.item_number == "347"
    assert d.auctioneer == "EDUARDO DE WERK"
    assert d.first_auction_date is not None


def test_parse_endereco_e_condicoes():
    d = _detail()
    assert d.postal_code == "14357-388"
    assert d.full_address is not None and "HENRIQUE DE FIGUEIREDO" in d.full_address
    assert d.accepts_fgts is True
    assert "FGTS" in d.payment_methods
    assert d.condo_fees_on_buyer is True
    assert d.taxes_on_buyer is True


def test_parse_documentos_e_fotos():
    d = _detail()
    assert d.registration_url is not None
    assert d.registration_url.endswith("/editais/matricula/SP/8787713989126.pdf")
    assert d.notice_url is not None
    assert d.notice_url.endswith("/editais/EA00240326CPVERE.PDF")
    assert d.photos == ["https://venda-imoveis.caixa.gov.br/fotos/F878771398912621.jpg"]


def test_data_convertida_para_utc():
    d = _detail()
    # 10h00 local BR -> 13h00 UTC (offset fixo de +3h).
    assert d.first_auction_date is not None
    assert d.first_auction_date.hour == 13
    assert d.first_auction_date.tzinfo is not None


def test_layout_inesperado_quando_pagina_vazia():
    with pytest.raises(LayoutInesperadoError):
        CaixaDetailParser().parse("<html><body>sem campos</body></html>", "x")


def test_deteccao_indisponivel():
    parser = CaixaDetailParser()
    assert parser.is_unavailable("<html>Imóvel não disponível</html>") is True
    assert parser.is_unavailable("<html>ok</html>") is False


def test_fonte_indisponivel_e_excecao():
    assert issubclass(FonteIndisponivelError, Exception)
