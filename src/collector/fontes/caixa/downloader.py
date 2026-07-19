from __future__ import annotations

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ...config import Settings
from ...logging import get_logger

log = get_logger(__name__)

class ErroTransitorio(Exception):
    """Falha transitória (429/5xx) que justifica retry."""


class ErroAntiBot(Exception):
    """A resposta não é o CSV: caímos num desafio anti-bot/WAF (ShieldSquare/PerfDrive).

    Normalmente indica bloqueio por reputação do IP (VPS/cloud/egress corporativo).
    Não adianta retry no mesmo IP — falha rápido com mensagem clara.
    """

_RETRY = retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ErroTransitorio, httpx.TransportError)),
)

# Headers de navegador real reduzem falso-positivo do anti-bot (não garantem passar).
_HEADERS_BROWSER = {
    "Accept": "text/csv,application/octet-stream,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Referer": "https://venda-imoveis.caixa.gov.br/sistema/busca-imovel.asp",
}


def _validar_conteudo_csv(resp: httpx.Response, url: str) -> None:
    """Garante que baixamos o CSV, e não a página de desafio anti-bot.

    Levanta ``ErroAntiBot`` (com dica de ação) em vez de deixar o pipeline
    parsear HTML e reportar tudo como ``invalidos``.
    """
    host = (resp.url.host or "").lower()
    if "caixa.gov.br" not in host:
        raise ErroAntiBot(
            f"Redirecionado para fora da Caixa ({resp.url}). Provável bloqueio anti-bot "
            f"(ShieldSquare/PerfDrive) do IP desta máquina ao baixar {url}. "
            "Tente por uma rede/IP residencial, use um CSV já baixado (--arquivo) "
            "ou um proxy de saída confiável."
        )

    ctype = resp.headers.get("content-type", "").lower()
    amostra = resp.content[:4096]
    amostra_low = amostra.lstrip().lower()
    parece_html = (
        "html" in ctype
        or amostra_low.startswith(b"<!doctype")
        or amostra_low.startswith(b"<html")
        or b"perfdrive" in amostra_low
        or b"shieldsquare" in amostra_low
        or b"validate.perfdrive" in amostra_low
    )
    if parece_html:
        raise ErroAntiBot(
            f"A resposta de {url} não é um CSV (parece HTML/desafio anti-bot; "
            f"content-type='{ctype or 'desconhecido'}', {len(resp.content)} bytes). "
            "Provável bloqueio por reputação de IP. Use --arquivo com um CSV baixado "
            "manualmente ou rode a partir de uma rede não bloqueada."
        )

    # O CSV da Caixa é ';'-delimitado; sem isso, não é o arquivo esperado.
    if b";" not in amostra:
        raise ErroAntiBot(
            f"Conteúdo de {url} não parece o CSV esperado (sem ';' no início, "
            f"{len(resp.content)} bytes). Provável página de bloqueio/erro."
        )


@_RETRY
def baixar_csv(uf: str, settings: Settings) -> bytes:
    url = settings.csv_url_template.format(uf=uf.upper())
    log.info("download.iniciando", uf=uf.upper(), url=url)

    headers = {"User-Agent": settings.user_agent, **_HEADERS_BROWSER}
    with httpx.Client(
        timeout=settings.request_timeout,
        verify=settings.verify_tls,
        headers=headers,
        follow_redirects=True,
    ) as client:
        resp = client.get(url)

        if resp.status_code == 429 or resp.status_code >= 500:
            raise ErroTransitorio(f"HTTP {resp.status_code} ao baixar {url}")
        resp.raise_for_status()

        _validar_conteudo_csv(resp, url)

        log.info("download.ok", uf=uf.upper(), bytes=len(resp.content))

        return resp.content
