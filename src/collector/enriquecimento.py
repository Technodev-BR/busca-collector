"""Enriquecimento de um imóvel (Fase 2): baixa o detalhe, parseia e envia ao backend.

Função pura de orquestração, reutilizada pelo consumidor RabbitMQ e pelo modo avulso da CLI.
"""
from __future__ import annotations

from .config import Settings
from .envio.api_client import ErroIngestao, IngestClient
from .fontes.caixa.detalhe import (
    AnomaliaParse,
    ImovelIndisponivel,
    baixar_detalhe,
    parsear_detalhe,
)
from .logging import get_logger

log = get_logger(__name__)


def enriquecer_imovel(
    codigo: str, settings: Settings, client: IngestClient, fonte: str = "caixa"
) -> str:
    """Coleta e envia o detalhe de um imóvel. Retorna o status ('ok'|'indisponivel').

    Lança ``ImovelIndisponivel`` (venda/remoção) e ``AnomaliaParse`` (layout) para que o
    chamador decida ack/nack. Erros transitórios já são reprocessados internamente (tenacity).
    """
    html = baixar_detalhe(codigo, settings)
    detalhe = parsear_detalhe(html, codigo)
    client.enviar_detalhe(codigo, detalhe, fonte=fonte)
    return "ok"


def enriquecer_avulso(codigo: str, settings: Settings, fonte: str = "caixa") -> str:
    with IngestClient(settings) as client:
        client.verificar_api_disponivel()
        try:
            return enriquecer_imovel(codigo, settings, client, fonte)
        except ImovelIndisponivel:
            log.warning("enriquecimento.indisponivel", codigo=codigo)
            return "indisponivel"
        except (AnomaliaParse, ErroIngestao) as e:
            log.error("enriquecimento.falha", codigo=codigo, erro=str(e))
            return "falha"
