# Collector (Python)

Serviço de **coleta** do Busca-Busca. Pipeline: **download → parse → normalize → enviar para a
API de ingestão** do backend. Não escreve direto no banco (ver
[ADR-0001](../docs/arquitetura/decisoes/0001-stack-tecnologica.md) e
[Collector (Python)](../docs/servicos/collector-python.md)).

## Requisitos
- Python **3.11+** (testado em 3.13).

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

Depois de instalar (`pip install -e .`), use o comando `collector`:

```bash
# baixa o CSV de SP e mostra estatísticas (sem enviar)
collector --uf SP --dry-run

# usa um CSV já baixado
collector --arquivo Lista_imoveis_SP.csv --dry-run

# proxy corporativo quebrando TLS? ignore a verificação (só em dev)
collector --uf SP --dry-run --insecure

# coleta e ENVIA ao backend (precisa do backend rodando e do token)
collector --uf SP
```

> Alternativa sem o atalho: `python -m collector.main --uf SP --dry-run`.

Configuração por ambiente (prefixo `COLLECTOR_`) — copie `.env.example` para `.env`:

| Variável | Default | Descrição |
|---|---|---|
| `COLLECTOR_BACKEND_BASE_URL` | `http://localhost:8080` | Base da API de ingestão |
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
  pyproject.toml
  src/collector/
    main.py                # CLI (entrypoint)
    config.py              # settings via env (pydantic-settings)
    logging.py        # logs estruturados (structlog)
    dominio/models.py      # ImovelColetado, LoteImoveis (pydantic)
    fontes/caixa/
      downloader.py        # baixa Lista_imoveis_{UF}.csv (httpx + tenacity)
      parser.py            # latin1, pula 2 linhas, ';', números BR
      mapper.py            # linha CSV -> ImovelColetado
    envio/api_client.py    # POST /internal/ingest/imoveis (X-Internal-Token + Idempotency-Key)
    pipeline.py            # orquestra a coleta por UF
  tests/                   # pytest (parser, mapper)
```

## Fases seguintes (a criar depois)
- **Enriquecimento por detalhe** (ADR-0010): baixa/parseia a página `detalhe-imovel.asp` e envia
  em `POST /internal/ingest/imoveis/{codigo}/detalhe`, acionado por um consumidor RabbitMQ.
- **Agendamento**: rodar `collector` ~1x/dia (o mais simples é o cron do container).

> Esses módulos ainda **não existem** no código — serão criados quando entrarmos nessas fases,
> conforme o desenho em [docs/servicos/collector-python.md](../docs/servicos/collector-python.md).
