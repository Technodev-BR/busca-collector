from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime

_COLUNAS: dict[str, tuple[str, ...]] = {
    "codigo": ("imóvel",),
    "uf": ("uf",),
    "cidade": ("cidade",),
    "bairro": ("bairro",),
    "endereco": ("endere",),
    "preco": ("preço",),
    "avaliacao": ("avalia",),
    "desconto": ("desconto",),
    "financiamento": ("financ",),
    "descricao": ("descri",),
    "modalidade": ("modalidade",),
    "link": ("link",),
}

_RE_DATA = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def brl_para_float(txt: str | None) -> float | None:
    if txt is None:
        return None
    s = txt.strip().replace(" ", "")
    if not s:
        return None
    # Se há vírgula, ela é o separador decimal e '.' é milhar.
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _achar_coluna(cabecalho: list[str], *chaves: str) -> str | None:
    for col in cabecalho:
        low = col.lower()
        if all(k in low for k in chaves):
            return col
    return None


def resolver_colunas(cabecalho: list[str]) -> dict[str, str | None]:
    return {
        chave: _achar_coluna(cabecalho, *chaves) for chave, chaves in _COLUNAS.items()
    }


def extrair_data_geracao(linhas: list[str]) -> date | None:
    for linha in linhas[:2]:
        m = _RE_DATA.search(linha)
        if m:
            try:
                return datetime.strptime(m.group(0), "%d/%m/%Y").date()
            except ValueError:
                continue
    return None


def parsear_csv(dados: bytes) -> tuple[date | None, list[dict[str, str]]]:
    texto = dados.decode("latin1")
    linhas = texto.splitlines()
    if len(linhas) < 4:
        raise ValueError("CSV com menos linhas que o esperado (layout mudou?).")

    data_geracao = extrair_data_geracao(linhas)
    corpo = "\n".join(linhas[2:])  # descarta título + linha em branco
    leitor = csv.reader(io.StringIO(corpo), delimiter=";")
    cabecalho = [c.strip() for c in next(leitor)]

    registros: list[dict[str, str]] = []
    for campos in leitor:
        if len(campos) < len(cabecalho):
            continue
        registros.append(
            {cabecalho[i]: campos[i].strip() for i in range(len(cabecalho))}
        )
    return data_geracao, registros
