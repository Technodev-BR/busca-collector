"""Orquestra a coleta em lote (CSV) por UF: download -> parse -> map -> envio.

Em ``dry_run`` não envia nada ao backend: só baixa/parseia/mapeia e calcula estatísticas
(útil para rodar localmente sem infraestrutura). Ver docs/servicos/collector-python.md.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

from .config import Settings
from .dominio.models import ImovelColetado, LoteImoveis
from .envio.api_client import IngestClient
from .fontes.caixa.downloader import baixar_csv
from .fontes.caixa.mapper import mapear, parse_descricao
from .fontes.caixa.parser import parsear_csv, resolver_colunas
from .logging import get_logger

log = get_logger(__name__)

# Namespace fixo p/ gerar Idempotency-Key determinístico por (fonte, uf, data, chunk).
_NS_IDEMPOTENCIA = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")


@dataclass
class ResumoColeta:
    uf: str
    gerado_em: date | None
    total_linhas: int = 0
    mapeados: int = 0
    invalidos: int = 0
    lotes_enviados: int = 0
    dry_run: bool = False
    tipos: dict[str, int] = field(default_factory=dict)

    def como_dict(self) -> dict:
        return {
            "uf": self.uf,
            "gerado_em": self.gerado_em.isoformat() if self.gerado_em else None,
            "total_linhas": self.total_linhas,
            "mapeados": self.mapeados,
            "invalidos": self.invalidos,
            "lotes_enviados": self.lotes_enviados,
            "dry_run": self.dry_run,
        }


def _lotes(imoveis: list[ImovelColetado], tamanho: int):
    for i in range(0, len(imoveis), tamanho):
        yield i // tamanho, imoveis[i : i + tamanho]


def _idempotency_key(fonte: str, uf: str, gerado_em: date, indice: int) -> str:
    nome = f"{fonte}:{uf}:{gerado_em.isoformat()}:{indice}"
    return str(uuid.uuid5(_NS_IDEMPOTENCIA, nome))


def _carregar_bytes(uf: str, settings: Settings, arquivo: str | None) -> bytes:
    if arquivo:
        log.info("fonte.arquivo", caminho=arquivo)
        with open(arquivo, "rb") as f:
            return f.read()
    return baixar_csv(uf, settings)


def coletar_uf(
    uf: str,
    settings: Settings,
    *,
    dry_run: bool = False,
    limite: int = 0,
    arquivo: str | None = None,
) -> ResumoColeta:
    dados = _carregar_bytes(uf, settings, arquivo)
    gerado_em, registros = parsear_csv(dados)
    if limite:
        registros = registros[:limite]

    resumo = ResumoColeta(uf=uf.upper(), gerado_em=gerado_em, dry_run=dry_run)
    resumo.total_linhas = len(registros)
    if not registros:
        log.warning("coleta.vazia", uf=uf.upper())
        return resumo

    colunas = resolver_colunas(list(registros[0].keys()))
    log.info("colunas.resolvidas", **{k: v for k, v in colunas.items() if v})

    imoveis: list[ImovelColetado] = []
    for registro in registros:
        imovel = mapear(registro, colunas, uf)
        if imovel is None:
            resumo.invalidos += 1
            continue
        imoveis.append(imovel)
        if dry_run:
            tipo = parse_descricao(imovel.descricao).get("tipo") or "(desconhecido)"
            resumo.tipos[str(tipo)] = resumo.tipos.get(str(tipo), 0) + 1

    resumo.mapeados = len(imoveis)

    if dry_run:
        log.info("dry_run.resumo", **resumo.como_dict())
        return resumo

    data_lote = gerado_em or date.today()
    with IngestClient(settings) as client:
        for indice, chunk in _lotes(imoveis, settings.batch_size):
            lote = LoteImoveis(
                fonte=settings.fonte, uf=uf.upper(), gerado_em=data_lote, imoveis=chunk
            )
            chave = _idempotency_key(settings.fonte, uf.upper(), data_lote, indice)
            client.enviar_lote(lote, chave)
            resumo.lotes_enviados += 1

    log.info("coleta.concluida", **resumo.como_dict())
    return resumo
