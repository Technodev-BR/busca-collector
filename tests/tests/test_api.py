from __future__ import annotations

import pytest

from collector.api.client import ApiClient
from collector.api.models import ApiRecord
from collector.core.exceptions import (
    ApiUnauthorizedException,
    ApiUnavailableException,
    ApiValidationException,
)
from collector.http.http import Http
from collector.http.models import HttpResponse


class _FakeHttp(Http):
    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.calls: list[dict] = []

    def get(self, url: str, **kwargs) -> HttpResponse:  # pragma: no cover - n?o usado
        raise NotImplementedError

    def post(self, url: str, **kwargs) -> HttpResponse:
        self.calls.append({"url": url, **kwargs})
        return HttpResponse(status_code=self.status, url=url, headers={}, content=b"")


def _records(n: int) -> list[ApiRecord]:
    return [ApiRecord(key=f"caixa:SP:{i}", payload={"item": {"code": str(i)}}) for i in range(n)]


def test_ingest_batch_envia_cada_registro(settings):
    http = _FakeHttp(status=200)
    ApiClient(settings, http).ingest_batch(_records(3))
    assert len(http.calls) == 3


def test_ingest_envia_idempotency_key(settings):
    http = _FakeHttp(status=200)
    ApiClient(settings, http).ingest(ApiRecord(key="caixa:SP:1", payload={"a": 1}))
    assert http.calls[0]["headers"]["Idempotency-Key"] == "caixa:SP:1"
    assert http.calls[0]["json"] == {"a": 1}


@pytest.mark.parametrize(
    ("status", "excecao"),
    [
        (400, ApiValidationException),
        (401, ApiUnauthorizedException),
        (500, ApiUnavailableException),
    ],
)
def test_validate_response_levanta(settings, status, excecao):
    http = _FakeHttp(status=status)
    with pytest.raises(excecao):
        ApiClient(settings, http).ingest(ApiRecord(key="k", payload={}))


def test_ingest_batch_loga_todos_antes_de_enviar(settings):
    """Mesmo falhando no envio, todos os payloads devem ter sido logados antes."""
    logados: list[str] = []

    class _Falha(_FakeHttp):
        def post(self, url: str, **kwargs) -> HttpResponse:
            raise ConnectionError("api fora")

    client = ApiClient(settings, _Falha())
    # Intercepta o logger interno para contar os eventos de payload.
    logger = client._ApiClient__logger  # type: ignore[attr-defined]
    original = logger.info

    def _spy(event: str, **kw):
        if event == "api.ingest.payload":
            logados.append(kw.get("key"))
        return original(event, **kw)

    logger.info = _spy  # type: ignore[method-assign]

    with pytest.raises(ConnectionError):
        client.ingest_batch(_records(5))

    assert logados == ["caixa:SP:0", "caixa:SP:1", "caixa:SP:2", "caixa:SP:3", "caixa:SP:4"]
