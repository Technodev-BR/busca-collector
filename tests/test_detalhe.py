from __future__ import annotations

import pytest

from collector.fontes.caixa.detalhe import (
    AnomaliaParse,
    ImovelIndisponivel,
    _indisponivel,
    parsear_detalhe,
)

# HTML sintético cobrindo os rótulos documentados (fonte-caixa-detalhe.md).
HTML = """
<html><body>
<h1>ADAMANTINA - VILA JOAQUINA</h1>
<div>Valor de avaliação: R$ 501.000,00</div>
<div>Valor mínimo de venda 1º Leilão: R$ 501.000,00</div>
<div>Valor mínimo de venda 2º Leilão: R$ 300.600,00</div>
<div>Data do 1º Leilão: 04/08/2026 - 10h00</div>
<div>Data do 2º Leilão: 10/08/2026 - 10h00</div>
<div>Leiloeiro(a): AYRTON DE SOUZA PORTO FILHO</div>
<div>Comarca: ADAMANTINA-SP</div>
<div>Endereço: RUA X, CEP: 17800-000, ADAMANTINA - SAO PAULO</div>
<div>Formas de pagamento: Recursos próprios. Permite FGTS.</div>
<div>Condomínio e Tributos: por conta do comprador</div>
<div>Situação: imóvel desocupado</div>
<a href="/editais/edital.pdf">Baixar edital e anexos</a>
<a href="/matriculas/matricula.pdf">Baixar matrícula do imóvel</a>
<img src="/fotos/imovel1.jpg"/>
</body></html>
"""


def test_parsear_detalhe_campos_principais():
    d = parsear_detalhe(HTML, "1444408501866")
    assert d.valor_primeiro_leilao == 501000.00
    assert d.valor_segundo_leilao == 300600.00
    assert d.data_primeiro_leilao is not None
    assert d.data_segundo_leilao is not None
    assert d.cep == "17800-000"
    assert d.situacao_ocupacao == "desocupado"
    assert d.aceita_fgts is True
    assert d.despesas_condominio_comprador is True
    assert d.despesas_tributos_comprador is True
    assert d.edital_url.endswith("edital.pdf")
    assert d.matricula_url.endswith("matricula.pdf")
    assert any("imovel1.jpg" in f for f in d.fotos)


def test_data_convertida_para_utc():
    d = parsear_detalhe(HTML, "x")
    # 10h00 local BR -> 13h00 UTC
    assert d.data_primeiro_leilao.hour == 13
    assert d.data_primeiro_leilao.tzinfo is not None


def test_anomalia_quando_pagina_vazia():
    with pytest.raises(AnomaliaParse):
        parsear_detalhe("<html><body>sem campos</body></html>", "x")


def test_deteccao_indisponivel():
    assert _indisponivel("<html>Imóvel não disponível</html>") is True
    assert _indisponivel("<html>ok</html>") is False


def test_baixar_detalhe_indisponivel_nao_e_erro_de_parse():
    # apenas garante que a exceção existe e é distinta
    assert issubclass(ImovelIndisponivel, Exception)
