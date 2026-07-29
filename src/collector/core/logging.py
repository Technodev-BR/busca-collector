from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import structlog


def configure_logging(
    level: str = "INFO",
    json_logs: bool = False,
    log_dir: str = "logs",
    retention_days: int = 7,
) -> None:
    level_no = logging.getLevelName(level.upper())

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level_no),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processor=(
                structlog.processors.JSONRenderer()
                if json_logs
                else structlog.dev.ConsoleRenderer()
            ),
        )
    )

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    # Rotaciona à meia-noite e mantém só os últimos `retention_days` arquivos
    # (os mais antigos são apagados automaticamente).
    arquivo = TimedRotatingFileHandler(
        filename=str(Path(log_dir) / "collector.log"),
        when="midnight",
        backupCount=retention_days,
        encoding="utf-8",
    )
    arquivo.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processor=(
                structlog.processors.JSONRenderer()
                if json_logs
                else structlog.dev.ConsoleRenderer(colors=False)
            ),
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(arquivo)
    root.setLevel(level_no)

    # Silencia o ruído de bibliotecas de terceiros no nível DEBUG.
    for noisy in ("httpx", "httpcore", "urllib3", "botocore", "boto3", "s3transfer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str = "collector") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
