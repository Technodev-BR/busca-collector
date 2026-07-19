"""Coleta e parsing da página de detalhe da Caixa (enriquecimento — Fase 2).

Coleta respeitosa: user-agent identificável, backoff em 429/5xx, pausa entre requisições
(configurável). O parsing é resiliente (tolera campos ausentes) e best-effort — o layout ASP
pode mudar; salvar amostras de HTML como fixtures ao evoluir
(ver docs/dados/fonte-caixa-detalhe.md).
"""
from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import httpx
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ...config import Settings
from ...dominio.models import DetalheImovel
from ...logging import get_logger

log = get_logger(__name__)

# Fuso de Brasília (as datas do site são horário local); convertemos para UTC de forma simples.
_OFFSET_BR_HORAS = 3


class ErroTransitorioDetalhe(Exception):
    """Falha transitória (429/5xx/rede) ao baixar o detalhe — justifica retry."""


class ImovelIndisponivel(Exception):
    """Página 404 ou 'imóvel não disponível' — sinaliza venda/remoção (sem retry)."""


class AnomaliaParse(Exception):
    """Página sem os campos esperados — possível mudança de layout (falhar/alertar)."""


_RETRY = retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ErroTransitorioDetalhe, httpx.TransportError)),
)


@_RETRY
def baixar_detalhe(codigo: str, settings: Settings) -> str:
    url = settings.detalhe_url_template.format(codigo=codigo)
    with httpx.Client(
        timeout=settings.request_timeout,
        verify=settings.verify_tls,
        headers={"User-Agent": settings.user_agent},
        follow_redirects=True,
    ) as client:
        resp = client.get(url)

        if resp.status_code == 404:
            raise ImovelIndisponivel(f"Detalhe 404 para {codigo}")
        if resp.status_code == 429 or resp.status_code >= 500:
            raise ErroTransitorioDetalhe(f"HTTP {resp.status_code} em {url}")
        resp.raise_for_status()

        html = resp.text
        if _indisponivel(html):
            raise ImovelIndisponivel(f"Página de indisponível para {codigo}")
        return html


def _indisponivel(html: str) -> bool:
    baixo = html.lower()
    return (
        "imóvel não disponível" in baixo
        or "imovel nao disponivel" in baixo
        or "não está mais disponível" in baixo
    )


def parsear_detalhe(html: str, codigo: str) -> DetalheImovel:
    soup = BeautifulSoup(html, "html.parser")
    texto = _normalizar(soup.get_text(separator="\n"))

    valor_aval = _valor_apos(texto, r"[Vv]alor de avalia[çc][ãa]o")
    valor_1 = _valor_apos(texto, r"1[ºo]\s*Leil[ãa]o")
    valor_2 = _valor_apos(texto, r"2[ºo]\s*Leil[ãa]o")

    detalhe = DetalheImovel(
        valor_primeiro_leilao=valor_1 or valor_aval,
        valor_segundo_leilao=valor_2,
        data_primeiro_leilao=_data_apos(texto, r"[Dd]ata\s+do\s+1[ºo]\s*Leil[ãa]o"),
        data_segundo_leilao=_data_apos(texto, r"[Dd]ata\s+do\s+2[ºo]\s*Leil[ãa]o"),
        leiloeiro=_texto_apos(texto, r"[Ll]eiloeiro\(?a?\)?"),
        edital=_texto_apos(texto, r"[Ee]dital"),
        numero_item=_texto_apos(texto, r"[Ii]tem"),
        matricula=_texto_apos(texto, r"[Mm]atr[íi]cula\(?s?\)?"),
        comarca=_texto_apos(texto, r"[Cc]omarca"),
        oficio=_texto_apos(texto, r"[Oo]f[íi]cio"),
        inscricao_imobiliaria=_texto_apos(texto, r"[Ii]nscri[çc][ãa]o\s+[Ii]mobili[áa]ria"),
        cep=_cep(texto),
        endereco_completo=_texto_apos(texto, r"[Ee]ndere[çc]o"),
        descricao_completa=_texto_apos(texto, r"[Dd]escri[çc][ãa]o"),
        situacao_ocupacao=_ocupacao(texto),
        edital_url=_link_por_texto(soup, "edital"),
        matricula_url=_link_por_texto(soup, "matrícula"),
        fotos=_fotos(soup),
    )
    _aplicar_pagamentos(detalhe, texto)
    _aplicar_despesas(detalhe, texto)

    if _tudo_vazio(detalhe):
        raise AnomaliaParse(f"Nenhum campo extraído para {codigo} (possível mudança de layout)")
    return detalhe


# ---------- helpers de parsing ----------

_MOEDA = re.compile(r"R\$\s*([\d.]+,\d{2})")
_DATA = re.compile(r"(\d{2})/(\d{2})/(\d{4})(?:\s*-\s*(\d{1,2})h(\d{2}))?")
_CEP = re.compile(r"CEP[:\s]*([0-9]{5}-?[0-9]{3})", re.IGNORECASE)


def _normalizar(texto: str) -> str:
    linhas = [ln.strip() for ln in texto.splitlines()]
    return "\n".join(ln for ln in linhas if ln)


def _linha_apos(texto: str, rotulo: str) -> str | None:
    m = re.search(rotulo + r"\s*[:\-]?\s*(.*)", texto)
    if not m:
        return None
    valor = m.group(1).strip()
    if not valor:
        # valor pode estar na linha seguinte
        resto = texto[m.end():].lstrip("\n")
        valor = resto.split("\n", 1)[0].strip() if resto else ""
    return valor or None


def _texto_apos(texto: str, rotulo: str) -> str | None:
    valor = _linha_apos(texto, rotulo)
    if not valor:
        return None
    valor = valor.strip(" .:-")
    return valor[:200] if valor else None


def _valor_apos(texto: str, rotulo: str) -> float | None:
    m = re.search(rotulo + r".{0,60}?" + _MOEDA.pattern, texto, re.DOTALL)
    if not m:
        return None
    return _moeda_para_float(m.group(1))


def _moeda_para_float(bruto: str) -> float | None:
    try:
        return float(bruto.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _data_apos(texto: str, rotulo: str) -> datetime | None:
    m = re.search(rotulo + r".{0,40}?" + _DATA.pattern, texto, re.DOTALL)
    if not m:
        return None
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hora = int(m.group(4)) if m.group(4) else 0
    minuto = int(m.group(5)) if m.group(5) else 0
    try:
        # horário local BR -> UTC (aproximação por offset fixo de -3h)
        local = datetime(ano, mes, dia, hora, minuto)
        return (local + timedelta(hours=_OFFSET_BR_HORAS)).replace(tzinfo=UTC)
    except ValueError:
        return None


def _cep(texto: str) -> str | None:
    m = _CEP.search(texto)
    return m.group(1) if m else None


def _ocupacao(texto: str) -> str | None:
    baixo = texto.lower()
    if "desocupado" in baixo:
        return "desocupado"
    if "ocupado" in baixo:
        return "ocupado"
    return None


def _aplicar_pagamentos(detalhe: DetalheImovel, texto: str) -> None:
    baixo = texto.lower()
    if "fgts" in baixo:
        detalhe.aceita_fgts = "permite fgts" in baixo or "fgts" in baixo
    if "financ" in baixo:
        nao_permite = "não permite financ" in baixo or "nao permite financ" in baixo
        detalhe.aceita_financiamento = not nao_permite


def _aplicar_despesas(detalhe: DetalheImovel, texto: str) -> None:
    baixo = texto.lower()
    if "condom" in baixo:
        detalhe.despesas_condominio_comprador = _por_conta_comprador(baixo, "condom")
    if "tributo" in baixo:
        detalhe.despesas_tributos_comprador = _por_conta_comprador(baixo, "tributo")


def _por_conta_comprador(texto: str, chave: str) -> bool:
    idx = texto.find(chave)
    if idx < 0:
        return False
    janela = texto[idx : idx + 120]
    return "comprador" in janela


def _link_por_texto(soup: BeautifulSoup, termo: str) -> str | None:
    termo = termo.lower()
    for a in soup.find_all("a", href=True):
        if termo in a.get_text(strip=True).lower():
            return a["href"]
    return None


def _fotos(soup: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(t in src.lower() for t in ("foto", "imovel", "galeria")):
            if src not in urls:
                urls.append(src)
    return urls


def _tudo_vazio(detalhe: DetalheImovel) -> bool:
    dados = detalhe.model_dump(exclude={"status_enriquecimento", "fotos"})
    return all(v is None for v in dados.values()) and not detalhe.fotos
