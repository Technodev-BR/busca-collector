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
    # Fonte Caixa (detalhe por imóvel — Fase 2)
    detalhe_url_template: str = (
        "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel={codigo}"
    )
    # UA de navegador real reduz o bloqueio anti-bot da Caixa; sobrescreva via
    # COLLECTOR_USER_AGENT se precisar identificar o coletor.
    user_agent: str = (
        "contato@technodevbr2.com"
    )

    # Comportamento
    request_timeout: float = 60.0
    batch_size: int = 500
    verify_tls: bool = True
    fonte: str = "caixa"

    # Enriquecimento: coleta respeitosa (pausa entre requisições, em segundos)
    detalhe_pausa_seg: float = 2.0

    # RabbitMQ (consumidor de enriquecimento — só usado no modo consumer)
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "buscabusca"
    rabbitmq_password: str = "buscabusca"
    rabbitmq_queue_enriquecimento: str = "imoveis.enriquecimento"
    rabbitmq_prefetch: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
