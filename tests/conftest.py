"""Fixtures de teste: um CSV de exemplo no formato real da Caixa (latin1)."""
from __future__ import annotations

import pytest

# 1ª linha: título com a data de geração. 2ª linha: em branco. 3ª: cabeçalho. Demais: dados.
_CSV = (
    "Lista de Imóveis da Caixa;Data de geração;15/07/2026\n"
    "\n"
    "N° do imóvel;UF;Cidade;Bairro;Endereço;Preço;Valor de avaliação;Desconto;"
    "Financiamento;Descrição;Modalidade de venda;Link de acesso\n"
    "1444408501866 ;SP ;ADAMANTINA ;VILA JOAQUINA ;ALAMEDA PADRE ANCHIETA, N. 1159 ;"
    "501.000,00;600.000,00;16.50;Não;"
    "Casa, 0.00 de área total, 171.43 de área privativa, 384.00 de área do terreno.;"
    "Leilão SFI - Edital único;"
    "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel=1444408501866\n"
    "8888888888888 ;SP ;SANTOS ;CENTRO ;RUA XV DE NOVEMBRO, 100 ;"
    "250.000,00;250.000,00;0.00;Sim;"
    "Apartamento, 62.00 de área privativa.;Venda Direta Online;"
    "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel=8888888888888\n"
)


@pytest.fixture
def csv_bytes() -> bytes:
    return _CSV.encode("latin1")
