from __future__ import annotations

from collector.core.constants import CaixaConstants
from collector.core.logging import get_logger
from collector.core.parsing import Br
from collector.sources.caixa.models import Analysis, AuctionRecord


class CaixaAnalysis:
    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    def process(self, records: list[AuctionRecord]) -> list[AuctionRecord]:
        for record in records:
            item = record.item
            detail = record.detail
            price = item.price
            appraisal = item.appraisal_value

            area = (detail.private_area or detail.total_area) if detail else None
            match = (
                CaixaConstants.AREA_PATTERN.search(item.description)
                if not area and item.description
                else None
            )
            if match:
                area = Br.numero(match.group(1))

            discount = item.discount_pct
            if discount is None and price and appraisal:
                discount = round((appraisal - price) / appraisal * 100, 2)

            record.analysis = Analysis(
                discount_pct=discount,
                price_m2=round(price / area, 2) if price and area else None,
                below_appraisal=bool(price and appraisal and price < appraisal),
            )

        self.__logger.info("caixa.analysis.finished", records=len(records))
        return records
