# Imagem standalone do coletor.
# O coletor CSV (entrypoint `collector`) fala HTTP com a API de ingestão e, opcionalmente,
# usa Redis (cache; degrada para memória se ausente) e S3/MinIO (storage; local é o padrão).
# Para subir Redis e MinIO junto, use o docker-compose.yml.

FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -e "." \
  && useradd --create-home --uid 10001 --shell /usr/sbin/nologin collector

USER collector

ENTRYPOINT ["collector"]
