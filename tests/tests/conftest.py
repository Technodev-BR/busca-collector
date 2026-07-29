"""Fixtures de teste: CSV de exemplo e Settings para testes unitários."""
from __future__ import annotations

import os

import pytest

# .env completo usado pelos testes de configuração (todas as COLLECTOR_* obrigatórias).
FULL_ENV_TEXT = """\
COLLECTOR_BACKEND_BASE_URL=http://teste:9999
COLLECTOR_INTERNAL_TOKEN=dev-internal-token
COLLECTOR_FONTE=caixa
COLLECTOR_CSV_URL_TEMPLATE=https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_{uf}.csv
COLLECTOR_DETALHE_URL_TEMPLATE=https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel={codigo}
COLLECTOR_USER_AGENT_BASE=busca-busca-collector/0.1
COLLECTOR_DATA_DIR=./data
COLLECTOR_S3_ENABLED=false
COLLECTOR_REDIS_ENABLED=false
COLLECTOR_REDIS_URL=redis://localhost:6379/0
COLLECTOR_REDIS_TTL_DIAS=30
COLLECTOR_REQUEST_TIMEOUT=60
COLLECTOR_VERIFY_TLS=true
COLLECTOR_DETALHAR_INLINE=true
COLLECTOR_DETALHE_LIMITE=0
COLLECTOR_DETALHE_PAUSA_SEG=2.0
COLLECTOR_LOCAL_RUN=false
COLLECTOR_LOG_LEVEL=INFO
COLLECTOR_JSON_LOGS=false
"""


def _bootstrap_env() -> None:
    if os.getenv("COLLECTOR_BACKEND_BASE_URL"):
        return
    for line in FULL_ENV_TEXT.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


_bootstrap_env()

from collector.core.settings import Settings  # noqa: E402 — após bootstrap do ambiente de teste

# 1ª linha: título com a data de geração. 2ª linha: em branco. 3ª: cabeçalho. Demais: dados.
_CSV = (
    "Lista de Imóveis da Caixa;Data de geração;15/07/2026\n"
    "\n"
    "N° do imóvel;UF;Cidade;Bairro;Endereço;Preço;Valor de avaliação;Desconto;"
    "Financiamento;Descrição;Modalidade de venda;Link de acesso\n"
    "1444408501866 ;SP ;ADAMANTINA ;VILA JOAQUINA ;ALAMEDA PADRE ANCHIETA, N. 1159 ;"
    "501.000,00;600.000,00;16.50;Não;"
    "Casa, 0.00 de área total, 171.43 de área privativa, 384.00 de área do terreno.;"
    "Leilão SFI - Edital único;"
    "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel=1444408501866\n"
    "8888888888888 ;SP ;SANTOS ;CENTRO ;RUA XV DE NOVEMBRO, 100 ;"
    "250.000,00;250.000,00;0.00;Sim;"
    "Apartamento, 62.00 de área privativa.;Venda Direta Online;"
    "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel=8888888888888\n"
)

# Valores usados só em testes — produção exige .env completo.
TEST_SETTINGS: dict = {
    "backend_base_url": "http://localhost:8080",
    "internal_token": "dev-internal-token",
    "fonte": "caixa",
    "csv_url_template": (
        "https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_{uf}.csv"
    ),
    "detalhe_url_template": (
        "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel={codigo}"
    ),
    "user_agent_base": "busca-busca-collector/0.1",
    "data_dir": "./data",
    "s3_enabled": False,
    "detalhar_inline": True,
    "detalhe_limite": 0,
    "redis_url": "redis://localhost:6379/0",
    "redis_enabled": False,
    "redis_ttl_dias": 30,
    "request_timeout": 60.0,
    "verify_tls": True,
    "detalhe_pausa_seg": 0.0,
    "local_run": False,
    "log_level": "INFO",
    "json_logs": False,
    "https_proxy": None,
}


@pytest.fixture
def csv_bytes() -> bytes:
    return _CSV.encode("latin1")


@pytest.fixture
def settings(tmp_path):
    return Settings(
        **{
            **TEST_SETTINGS,
            "data_dir": str(tmp_path / "data"),
            "detalhe_pausa_seg": 0,
            "redis_enabled": False,
        }
    )
