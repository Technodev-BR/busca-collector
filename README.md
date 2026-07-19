# Collector (Python)

Serviço de **coleta** do Busca-Busca. Pipeline: **download → parse → normalize → (opcional)
enviar para a API de ingestão**.

## Desacoplamento

| Este serviço | Precisa de |
|---|---|
| `--dry-run` | Só internet (CSV da Caixa). **Sem** API, banco, fila, Redis. |
| Envio real | Só HTTP na API (`busca-backend`). **Sem** Postgres/Rabbit/Redis. |

Antes de enviar, o coletor chama `GET /actuator/health`. Se a API estiver fora, aborta com
erro claro — não depende de Compose compartilhado.

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

> Também funciona com [uv](https://docs.astral.sh/uv/): `uv sync` / `uv run ...`.

## Executar localmente

O modo `--dry-run` **não precisa do backend nem de infraestrutura**: baixa o CSV oficial da
Caixa, parseia e mapeia, e imprime estatísticas.

```bash
# baixa o CSV de SP e mostra estatísticas (sem enviar)
collector --uf SP --dry-run

# usa um CSV já baixado
collector --arquivo Lista_imoveis_SP.csv --dry-run

# proxy corporativo quebrando TLS? ignore a verificação (só em dev)
collector --uf SP --dry-run --insecure

# coleta e ENVIA ao backend (API precisa estar rodando)
collector --uf SP
```

> Alternativa sem o atalho: `python -m collector.main --uf SP --dry-run`.

## Docker (standalone)

```bash
# build
docker build -t busca-collector:local .

# dry-run (default do Dockerfile / Compose) — zero dependência de outros serviços
docker compose run --rm collector --uf SP --dry-run

# envio real — API no host (busca-backend compose na porta 8080)
docker compose run --rm collector --uf SP --limite 50
```

A URL padrão no Compose do coletor é `http://host.docker.internal:8080` (API no host).
Ajuste com `COLLECTOR_BACKEND_BASE_URL` se a API estiver em outra rede/host.

Configuração por ambiente (prefixo `COLLECTOR_`) — copie `.env.example` para `.env`:

| Variável | Default | Descrição |
|---|---|---|
| `COLLECTOR_BACKEND_BASE_URL` | `http://localhost:8080` | Base da API de ingestão (só no envio) |
| `COLLECTOR_INTERNAL_TOKEN` | `dev-internal-token` | Header `X-Internal-Token` |
| `COLLECTOR_CSV_URL_TEMPLATE` | URL da Caixa | `{uf}` é substituído pela UF |
| `COLLECTOR_BATCH_SIZE` | `500` | Tamanho do lote de envio |
| `COLLECTOR_VERIFY_TLS` | `true` | Verificação de certificado TLS |


## Testes e qualidade

Requer as dependências de desenvolvimento (`pip install -e ".[dev]"`).

### Testes (pytest)

```bash
pytest              # todos os testes
pytest -v           # saída detalhada
pytest tests/test_parser.py   # um arquivo específico
```

### Lint (ruff)

O [Ruff](https://docs.astral.sh/ruff/) verifica estilo, imports e erros comuns. A configuração
está em `pyproject.toml` (`line-length = 100`, regras `E`, `F`, `I`, `UP`, `B`).

```bash
ruff check .                    # verifica o projeto inteiro
ruff check src/collector        # só o código-fonte
ruff check . --fix              # corrige automaticamente o que for possível
ruff check src/collector/main.py   # um arquivo específico
```

### Tipos (mypy)

O [mypy](https://mypy.readthedocs.io/) valida anotações de tipo em `src/`. A configuração está em
`pyproject.toml` (`python_version = 3.11`, plugin `pydantic.mypy`).

```bash
mypy src                        # verifica todo o código-fonte
mypy src/collector/main.py      # um arquivo específico
```

### Rodar tudo de uma vez

```bash
pytest && ruff check . && mypy src
```

### Pelo VS Code / Cursor

Com a pasta do projeto aberta, use **Run and Debug** (`.vscode/launch.json`):

| Configuração | O que faz |
|---|---|
| `Pytest: todos os testes` | roda `pytest tests -v` |
| `Pytest: arquivo atual` | roda pytest no arquivo aberto |
| `Ruff: check (projeto)` | roda `ruff check .` |
| `Ruff: check (arquivo atual)` | roda ruff no arquivo aberto |
| `Ruff: fix (projeto)` | roda `ruff check . --fix` |
| `Mypy: check (src)` | roda `mypy src` |
| `Mypy: check (arquivo atual)` | roda mypy no arquivo aberto |

Extensões recomendadas em `.vscode/extensions.json`: Python, Pylance, Ruff, Mypy Type Checker.

## Estrutura

```
busca-collector/
  Dockerfile               # imagem standalone
  docker-compose.yml       # só o job do coletor (sem API/banco/fila)
  pyproject.toml
  src/collector/
    main.py                # CLI (entrypoint)
    config.py              # settings via env (pydantic-settings)
    logging.py             # logs estruturados (structlog)
    dominio/models.py      # ImovelColetado, LoteImoveis (pydantic)
    fontes/caixa/
      downloader.py        # baixa Lista_imoveis_{UF}.csv (httpx + tenacity)
      parser.py            # latin1, pula 2 linhas, ';', números BR
      mapper.py            # linha CSV -> ImovelColetado
    envio/api_client.py    # health + POST /internal/ingest/imoveis
    pipeline.py            # orquestra a coleta por UF
  tests/                   # pytest (parser, mapper)
```

## Fases seguintes (a criar depois)
- **Enriquecimento por detalhe** (ADR-0010): baixa/parseia a página `detalhe-imovel.asp` e envia
  em `POST /internal/ingest/imoveis/{codigo}/detalhe`, acionado por um consumidor RabbitMQ.
- **Agendamento**: rodar `collector` ~1x/dia (o mais simples é o cron do container).

> Esses módulos ainda **não existem** no código — serão criados quando entrarmos nessas fases,
> conforme o desenho em [docs/servicos/collector-python.md](../docs/servicos/collector-python.md).
