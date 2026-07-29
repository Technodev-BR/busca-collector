from __future__ import annotations

import re


class Br:
    @staticmethod
    def numero(bruto: object) -> float | None:
        if bruto is None or isinstance(bruto, bool):
            return None
        if isinstance(bruto, (int, float)):
            return float(bruto)
        limpo = str(bruto).strip()
        if not limpo:
            return None
        try:
            # Formato BR: vírgula é decimal, ponto é milhar.
            return float(limpo.replace(".", "").replace(",", ".")) if "," in limpo else float(limpo)
        except ValueError:
            return None

    @staticmethod
    def moeda(bruto: object) -> float | None:
        if bruto is None or isinstance(bruto, bool):
            return None
        if isinstance(bruto, (int, float)):
            return float(bruto)
        return Br.numero(str(bruto).replace("R$", "").replace("%", ""))

    @staticmethod
    def booleano(bruto: object) -> bool | None:
        if isinstance(bruto, bool):
            return bruto
        if bruto is None:
            return None
        s = str(bruto).strip().lower()
        if s in ("sim", "s", "true", "1"):
            return True
        if s in ("não", "nao", "n", "false", "0"):
            return False
        return None

    @staticmethod
    def inteiro(bruto: object) -> int | None:
        if bruto is None or isinstance(bruto, bool):
            return None
        if isinstance(bruto, int):
            return bruto
        m = re.search(r"\d+", str(bruto))
        return int(m.group()) if m else None

    @staticmethod
    def area(bruto: object) -> float | None:
        if bruto is None:
            return None
        m = re.search(r"[\d.,]+", str(bruto))
        return Br.numero(m.group()) if m else None

    @staticmethod
    def texto(bruto: object) -> str | None:
        if not bruto:
            return None
        valor = " ".join(str(bruto).split())
        return valor or None
