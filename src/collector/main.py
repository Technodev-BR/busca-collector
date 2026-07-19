"""Ponto de entrada da CLI do coletor.

Depois de instalar (``pip install -e .``), rode pelo atalho ``collector``:
    collector --uf SP --dry-run          # baixa/parseia/mapeia, sem enviar
    collector --uf SP                     # coleta e envia ao backend
    collector --arquivo Lista_imoveis_SP.csv --dry-run
    collector --uf RJ --insecure          # ignora TLS (proxy corporativo)

Também funciona como módulo: ``python -m collector.main --uf SP --dry-run``.
"""
from __future__ import annotations

import argparse
import sys

from .config import get_settings
from .logging import configure_logging, get_logger
from .pipeline import coletar_uf

log = get_logger("collector.cli")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="collector", description="Coletor de imóveis (CSV oficial da Caixa)."
    )
    ap.add_argument("--uf", default="SP", help="UF a coletar (default: SP)")
    ap.add_argument("--arquivo", help="Usa um CSV já baixado em vez de baixar da Caixa")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Não envia ao backend; só baixa/parseia/mapeia e mostra estatísticas",
    )
    ap.add_argument(
        "--limite", type=int, default=0, help="Processa só os N primeiros (0 = todos)"
    )
    ap.add_argument("--batch-size", type=int, help="Tamanho do lote de envio")
    ap.add_argument(
        "--insecure", action="store_true", help="Ignora verificação TLS (proxy corporativo)"
    )
    ap.add_argument("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR")
    ap.add_argument("--json-logs", action="store_true", help="Logs em JSON (produção)")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    configure_logging(level=args.log_level, json_logs=args.json_logs)

    settings = get_settings()
    if args.insecure:
        settings.verify_tls = False
    if args.batch_size:
        settings.batch_size = args.batch_size

    try:
        resumo = coletar_uf(
            args.uf,
            settings,
            dry_run=args.dry_run,
            limite=args.limite,
            arquivo=args.arquivo,
        )
    except FileNotFoundError as e:
        log.error("arquivo.nao_encontrado", erro=str(e))
        return 2
    except Exception as e:  # noqa: BLE001 - fronteira da CLI: loga e sai com código != 0
        log.error("coleta.falhou", erro=str(e), tipo=type(e).__name__)
        return 1

    if args.dry_run and resumo.tipos:
        top = sorted(resumo.tipos.items(), key=lambda kv: kv[1], reverse=True)[:8]
        log.info("dry_run.tipos", **{tipo: qtd for tipo, qtd in top})
    return 0


if __name__ == "__main__":
    sys.exit(main())
