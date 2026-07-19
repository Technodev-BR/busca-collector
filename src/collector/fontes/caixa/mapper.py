from __future__ import annotations

import re

from ...dominio.models import ImovelColetado
from .parser import brl_para_float

_RE_AREA = {
    "area_total": re.compile(r"([\d.,]+)\s*de\s*área\s*total", re.IGNORECASE),
    "area_privativa": re.compile(r"([\d.,]+)\s*de\s*área\s*privativa", re.IGNORECASE),
    "area_terreno": re.compile(r"([\d.,]+)\s*de\s*área\s*(?:do\s*)?terreno", re.IGNORECASE),
}


def _bool_br(txt: str | None) -> bool | None:
    if txt is None:
        return None
    s = txt.strip().lower()
    if s in ("sim", "s", "true", "1"):
        return True
    if s in ("não", "nao", "n", "false", "0"):
        return False
    return None


def _area_para_float(txt: str) -> float | None:
    # Áreas no CSV usam ponto decimal (ex.: "171.43"); não é formato milhar BR.
    try:
        return float(txt.replace(".", "").replace(",", ".")) if "," in txt else float(txt)
    except ValueError:
        return None


def parse_descricao(descricao: str | None) -> dict[str, float | str | None]:
    if not descricao:
        return {"tipo": None, "area_total": None, "area_privativa": None, "area_terreno": None}
    tipo = descricao.split(",", 1)[0].strip() or None
    resultado: dict[str, float | str | None] = {"tipo": tipo}
    for chave, regex in _RE_AREA.items():
        m = regex.search(descricao)
        resultado[chave] = _area_para_float(m.group(1)) if m else None
    return resultado


def _get(registro: dict[str, str], coluna: str | None) -> str | None:
    if not coluna:
        return None
    valor = registro.get(coluna)
    return valor.strip() if isinstance(valor, str) else valor


def mapear(
    registro: dict[str, str],
    colunas: dict[str, str | None],
    uf_default: str,
) -> ImovelColetado | None:
    codigo = _get(registro, colunas.get("codigo"))
    if not codigo:
        return None

    return ImovelColetado(
        codigo=codigo,
        uf=(_get(registro, colunas.get("uf")) or uf_default).upper(),
        cidade=_get(registro, colunas.get("cidade")) or "",
        bairro=_get(registro, colunas.get("bairro")),
        endereco=_get(registro, colunas.get("endereco")),
        preco=brl_para_float(_get(registro, colunas.get("preco"))),
        valor_avaliacao=brl_para_float(_get(registro, colunas.get("avaliacao"))),
        desconto_pct=brl_para_float(_get(registro, colunas.get("desconto"))),
        financiamento=_bool_br(_get(registro, colunas.get("financiamento"))),
        descricao=_get(registro, colunas.get("descricao")),
        modalidade=_get(registro, colunas.get("modalidade")) or "",
        link=_get(registro, colunas.get("link")) or "",
    )
