from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from collector.core.settings import Settings
from tests.conftest import FULL_ENV_TEXT


def _clear_collector_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("COLLECTOR_"):
            monkeypatch.delenv(key, raising=False)


def test_settings_ausente(tmp_path, monkeypatch: pytest.MonkeyPatch):
    # Diretório vazio (sem .env) para não herdar o .env do projeto.
    monkeypatch.chdir(tmp_path)
    _clear_collector_env(monkeypatch)
    with pytest.raises(ValidationError):
        Settings()


def test_settings_carrega_dotenv(tmp_path, monkeypatch: pytest.MonkeyPatch):
    env = tmp_path / ".env"
    env.write_text(FULL_ENV_TEXT, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    _clear_collector_env(monkeypatch)

    cfg = Settings()
    assert cfg.backend_base_url == "http://teste:9999"
    assert cfg.redis_enabled is False
    assert cfg.redis_ttl_dias == 30
    assert cfg.s3_enabled is False


def test_processo_tem_prioridade_sobre_dotenv(tmp_path, monkeypatch: pytest.MonkeyPatch):
    env = tmp_path / ".env"
    env.write_text(FULL_ENV_TEXT, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    _clear_collector_env(monkeypatch)
    monkeypatch.setenv("COLLECTOR_BACKEND_BASE_URL", "http://processo:2")

    cfg = Settings()
    assert cfg.backend_base_url == "http://processo:2"


def test_settings_int_invalido(tmp_path, monkeypatch: pytest.MonkeyPatch):
    env = tmp_path / ".env"
    env.write_text(
        FULL_ENV_TEXT.replace("COLLECTOR_REDIS_TTL_DIAS=30", "COLLECTOR_REDIS_TTL_DIAS=nao-numero"),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    _clear_collector_env(monkeypatch)

    with pytest.raises(ValidationError):
        Settings()
