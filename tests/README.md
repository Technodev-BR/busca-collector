# Collector (Python)

Serviço de **coleta** de imóveis do Busca-Busca (leilões da Caixa). Pipeline único:

**baixar CSVs (todas as UFs) → salvar (local ou S3) → parse → enriquecer detalhe (inline) → análise → ingerir na API**.

## Arquitetura

O código segue injeção de dependência: cada camada expõe uma interface (`Storage`, `Cache`,
`Http`, `Api`, `Source`) e uma função `configure_*` que constrói a implementação a partir das
`Settings`. O `setup()` monta tudo e devolve um `Pipeline`.

```
src/collector/
  main.py                # entrypoint (chama setup() + runner.run)
  setup.py               # injeção de dependência (configure_* → Pipeline)
  pipeline.py            # coleta -> monta ApiRecord -> ingere
  core/
    settings.py          # Settings (pydantic-settings, prefixo COLLECTOR_)
    logging.py           # structlog + arquivo rotativo em logs/
    runner.py            # fronteira do processo (trata exceções -> exit code)
    exceptions.py        # AppException e derivadas
    enums.py             # ErrorCode, StorageDirectory, DetailStatus, ...
    parsing.py           # Br: coerção de número/moeda/booleano/área (formato BR)
    constants.py         # CaixaConstants (URLs, UFs, regex)
  http/                  # HttpClient (httpx + retry) + HttpSession (UA/cookies)
  storage/               # LocalStorage (padrão) e S3Storage (boto3/MinIO)
  cache/                 # MemoryCache (padrão) e RedisCache
  api/                   # ApiClient (ingestão via HTTP)
  sources/
    source.py            # interface Source
    caixa/
      source.py          # orquestra download -> parse -> enrich -> analysis
      parser.py          # CaixaParser (CSV) e CaixaDetailParser (HTML)
      enricher.py        # busca a ficha do imóvel (com cache/fingerprint)
      analysis.py        # desconto, preço/m², abaixo da avaliação
      models.py          # CaixaItem, CaixaDetail, Analysis, AuctionRecord
tests/
```

## Fluxo

1. Baixa `Lista_imoveis_{UF}.csv` da Caixa para **todas as UFs** (User-Agent com id aleatório por
   processo).
2. Salva os CSVs no storage (`LocalStorage` por padrão; `S3Storage` se `COLLECTOR_S3_ENABLED=true`).
3. Faz o parse de cada linha → `CaixaItem` (coerção de valores no formato BR via `Br`).
4. **Enriquecimento inline** (`COLLECTOR_DETALHAR_INLINE=true`): para cada imóvel (até
   `COLLECTOR_DETALHE_LIMITE`, `0` = sem limite) baixa a ficha e preenche o `CaixaDetail`. Um
   *fingerprint* dos campos relevantes é gravado no cache para evitar re-buscar o que não mudou.
5. Análise: calcula desconto, preço/m² e se está abaixo da avaliação.
6. **Ingestão**: cada `AuctionRecord` vira um `ApiRecord` e é enviado via `POST` para a API. Antes
   de enviar, **o payload de cada registro é gravado no log** (evento `api.ingest.payload`) — útil
   para inspecionar os dados mesmo quando a API está fora.

> Se a API estiver indisponível, o `POST` falha com erro de conexão e o `runner` encerra com código
> de saída claro. Não é necessário nenhum modo/flag especial: os payloads já foram logados antes.

## Requisitos

- Python **3.11+** (testado em 3.13), **ou** Docker.

## Instalação (venv + pip)

```bash
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

pip install -e ".[dev]"
```

## Executar localmente

A configuração é por ambiente (prefixo `COLLECTOR_`). Copie o exemplo e ajuste:

```bash
cp .env.example .env
```

Rode o coletor:

```bash
python -m collector.main
# ou, se o entrypoint estiver no PATH:
collector
```

Modos de origem do CSV (a ingestão à API acontece nos dois):

- `COLLECTOR_LOCAL_RUN=false` — **baixa** o CSV de cada UF da Caixa, salva no storage e segue o
  pipeline.
- `COLLECTOR_LOCAL_RUN=true` — **lê os CSVs já salvos** no storage (pasta `downloads/caixa` em
  `COLLECTOR_DATA_DIR`) em vez de baixar. Útil para reprocessar ou quando o anti-bot bloqueia o
  download.

### Testar sem backend, Redis ou Docker

Basta deixar `COLLECTOR_S3_ENABLED=false` e `COLLECTOR_REDIS_ENABLED=false` (storage em disco e
cache em memória). Mesmo com a API fora, o coletor grava no log todos os payloads que tentaria
ingerir e depois mostra o erro de conexão com a API.

## Docker

O `docker-compose.yml` sobe o coletor junto de **Redis** (cache) e **MinIO** (storage S3-compatível),
criando o bucket automaticamente. A stack usa a rede externa `buscabusca` (fale com o backend por
`http://backend:8080`).

```bash
# rede compartilhada (se ainda não existir)
docker network create buscabusca

cp .env.example .env
# COLLECTOR_INTERNAL_TOKEN deve bater com o token do backend

docker compose run --rm collector
```

Para uma imagem standalone (sem Redis/MinIO), use apenas o `Dockerfile` (cache degrada para memória
e storage é local).

## Configuração (variáveis `COLLECTOR_*`)

O coletor **não tem defaults no código** para as variáveis obrigatórias — defina-as no `.env` (ou no
ambiente do processo, que tem prioridade sobre o arquivo).

| Variável | Descrição |
|---|---|
| `COLLECTOR_BACKEND_BASE_URL` | Base da API de ingestão |
| `COLLECTOR_INTERNAL_TOKEN` | Header `X-Internal-Token` |
| `COLLECTOR_FONTE` | Identificador da fonte (ex.: `caixa`) |
| `COLLECTOR_CSV_URL_TEMPLATE` | URL do CSV (`{uf}` substituído pela UF) |
| `COLLECTOR_DETALHE_URL_TEMPLATE` | URL da ficha (`{codigo}` substituído) |
| `COLLECTOR_USER_AGENT_BASE` | Nome-base do UA (+ id aleatório por processo) |
| `COLLECTOR_DATA_DIR` | Diretório raiz do storage local |
| `COLLECTOR_S3_ENABLED` | `true` = usa S3/MinIO; `false` = storage local |
| `COLLECTOR_S3_BUCKET` / `_REGION` / `_ENDPOINT_URL` | Config do bucket S3 (MinIO usa `endpoint_url`) |
| `COLLECTOR_S3_ACCESS_KEY` / `_SECRET_KEY` | Credenciais do S3/MinIO |
| `COLLECTOR_REDIS_ENABLED` | `true` = cache no Redis; `false` = cache em memória |
| `COLLECTOR_REDIS_URL` | URL do Redis |
| `COLLECTOR_REDIS_TTL_DIAS` | TTL das chaves de fingerprint |
| `COLLECTOR_REQUEST_TIMEOUT` | Timeout HTTP (segundos) |
| `COLLECTOR_VERIFY_TLS` | Verificação de certificado TLS |
| `COLLECTOR_HTTPS_PROXY` | Proxy de saída (anti-bot), opcional |
| `COLLECTOR_DETALHAR_INLINE` | `true` = enriquece detalhe no mesmo processo |
| `COLLECTOR_DETALHE_LIMITE` | Máx. de detalhes a buscar (`0` = sem limite) |
| `COLLECTOR_DETALHE_PAUSA_SEG` | Pausa entre requisições de detalhe (segundos) |
| `COLLECTOR_LOCAL_RUN` | `true` = lê CSVs salvos; `false` = baixa da fonte |
| `COLLECTOR_LOG_LEVEL` | Nível de log (`DEBUG`, `INFO`, ...) |
| `COLLECTOR_JSON_LOGS` | `true` = logs em JSON; `false` = console colorido |
| `COLLECTOR_LOG_DIR` | Pasta dos arquivos de log (rotação diária) |
| `COLLECTOR_LOG_RETENTION_DAYS` | Dias de retenção dos logs |

## Testes e qualidade

Requer as dependências de desenvolvimento (`pip install -e ".[dev]"`).

### Testes (pytest)

```bash
pytest              # todos os testes
pytest -v           # saída detalhada
pytest tests/test_parser.py   # um arquivo específico
```

### Lint (ruff)

```bash
ruff check .                    # verifica o projeto inteiro
ruff check . --fix              # corrige o que for possível
```

### Tipos (mypy)

```bash
mypy src
```

### Rodar tudo de uma vez

```bash
pytest && ruff check . && mypy src
```

### Pelo VS Code / Cursor

Com a pasta do projeto aberta, use **Run and Debug** (`.vscode/launch.json`):

| Configuração | O que faz |
|---|---|
| `Collector: baixar e ingerir` | roda `collector.main` com `COLLECTOR_LOCAL_RUN=false` |
| `Collector: local (lê CSVs salvos)` | roda `collector.main` com `COLLECTOR_LOCAL_RUN=true` |
| `Pytest: todos os testes` | roda `pytest tests -v` |
| `Pytest: arquivo atual` | roda pytest no arquivo aberto |

Extensões recomendadas em `.vscode/extensions.json`: Python, Pylance, Ruff, Mypy Type Checker.
