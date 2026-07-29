from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="COLLECTOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    backend_base_url: str
    internal_token: str

    fonte: str
    csv_url_template: str
    detalhe_url_template: str
    user_agent_base: str

    data_dir: str
    s3_enabled: bool = False
    s3_bucket: str | None = None
    s3_region: str | None = None
    s3_endpoint_url: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None

    redis_url: str
    redis_enabled: bool
    redis_ttl_dias: int

    request_timeout: float
    verify_tls: bool
    https_proxy: str | None = None

    detalhar_inline: bool = True
    detalhe_limite: int = 0
    detalhe_pausa_seg: float

    local_run: bool
    log_level: str
    json_logs: bool
    log_dir: str = "logs"
    log_retention_days: int = 7


@lru_cache
def configure_settings() -> Settings:
    return Settings()
