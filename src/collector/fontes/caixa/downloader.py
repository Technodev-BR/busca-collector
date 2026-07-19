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

_RETRY = retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ErroTransitorio, httpx.TransportError)),
)

@_RETRY
def baixar_csv(uf: str, settings: Settings) -> bytes:
    url = settings.csv_url_template.format(uf=uf.upper())
    log.info("download.iniciando", uf=uf.upper(), url=url)

    with httpx.Client(
        timeout=settings.request_timeout,
        verify=settings.verify_tls,
        headers={"User-Agent": settings.user_agent},
        follow_redirects=True,
    ) as client:
        resp = client.get(url)
        
        if resp.status_code == 429 or resp.status_code >= 500:
            raise ErroTransitorio(f"HTTP {resp.status_code} ao baixar {url}")
        resp.raise_for_status()

        log.info("download.ok", uf=uf.upper(), bytes=len(resp.content))

        return resp.content
