from __future__ import annotations

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import Settings
from ..dominio.models import LoteImoveis
from ..logging import get_logger

log = get_logger(__name__)

class ErroIngestao(Exception):
    """Falha permanente ao enviar um lote (status inesperado)."""


class ErroTransitorio(Exception):
    """Falha transitória (rede/429/5xx) — justifica retry."""


class IngestClient:
    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._client = httpx.Client(
            base_url=settings.backend_base_url,
            timeout=settings.request_timeout,
            verify=settings.verify_tls,
            headers={
                "User-Agent": settings.user_agent,
                "X-Internal-Token": settings.internal_token,
                "Content-Type": "application/json",
            },
        )

    def __enter__(self) -> IngestClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ErroTransitorio, httpx.TransportError)),
    )
    def enviar_lote(self, lote: LoteImoveis, idempotency_key: str) -> dict:
        payload = lote.model_dump(by_alias=True, mode="json")
        resp = self._client.post(
            "/internal/ingest/imoveis",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        )

        if resp.status_code == 429 or resp.status_code >= 500:
            raise ErroTransitorio(f"HTTP {resp.status_code} na ingestão")

        if resp.status_code != 202:
            raise ErroIngestao(
                f"Status inesperado {resp.status_code}: {resp.text[:300]}"
            )

        log.info(
            "ingestao.ok",
            uf=lote.uf,
            itens=len(lote.imoveis),
            idempotency_key=idempotency_key,
        )
        
        try:
            return resp.json()
        except ValueError:
            return {}
