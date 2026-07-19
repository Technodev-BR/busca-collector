"""Configuração via variáveis de ambiente (pydantic-settings).

Todas as chaves usam o prefixo COLLECTOR_ e podem vir de um arquivo .env.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="COLLECTOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Backend (API de ingestão)
    backend_base_url: str = "http://localhost:8080"
    internal_token: str = "dev-internal-token"

    # Fonte Caixa (CSV)
    csv_url_template: str = (
        "https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_{uf}.csv"
    )
    user_agent: str = "busca-busca-collector/0.1 (+contato: dev@technodevbr.com)"

    # Comportamento
    request_timeout: float = 60.0
    batch_size: int = 500
    verify_tls: bool = True
    fonte: str = "caixa"


@lru_cache
def get_settings() -> Settings:
    return Settings()
