# Imagem standalone do coletor.
# O coletor CSV (entrypoint `collector`) não depende de Postgres, Redis nem RabbitMQ — só HTTP
# na API de ingestão quando NÃO está em --dry-run. O modo consumer (entrypoint
# `collector-enriquecer`) usa RabbitMQ (extra `consumer`, incluído aqui na mesma imagem).

FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -e ".[consumer]" \
  && useradd --create-home --uid 10001 --shell /usr/sbin/nologin collector

USER collector

ENTRYPOINT ["collector"]
# Default seguro: dry-run (não fala com a API)
CMD ["--uf", "SP", "--dry-run"]
