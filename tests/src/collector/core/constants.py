from __future__ import annotations

import re

from collector.core.enums import StorageDirectory


class CaixaConstants:
    BASE_URL = "https://venda-imoveis.caixa.gov.br"

    DOWNLOAD_DIR = StorageDirectory.CAIXA_DOWNLOAD
    FILE_NAME = "{uf}.csv"

    # Fuso de Brasília: datas do site são horário local; somamos o offset para chegar a UTC.
    BR_UTC_OFFSET_HOURS = 3

    UFS_BR: tuple[str, ...] = (
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
        "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
    )

    CSV_ACCEPT = "text/csv,application/csv,*/*;q=0.8"
    DETAIL_ACCEPT = "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"

    AREA_PATTERN = re.compile(r"([\d.,]+)\s*de\s*área\s*(?:privativa|total)", re.IGNORECASE)
    MONEY_PATTERN = re.compile(r"R\$\s*([\d.]+,\d{2})")
    DATE_PATTERN = re.compile(r"(\d{2})/(\d{2})/(\d{4})(?:\s*-\s*(\d{1,2})h(\d{2}))?")
    CEP_PATTERN = re.compile(r"CEP[:\s]*([0-9]{5}-?[0-9]{3})", re.IGNORECASE)
    EXIBEDOC_PATTERN = re.compile(r"ExibeDoc\('([^']+)'\)")
