from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict
from pydantic.alias_generators import to_camel

from collector.core.enums import DetailStatus, OccupancyStatus
from collector.core.parsing import Br

# Aceitam string crua (formato BR) ou valor já tipado, coagindo na entrada.
BrMoney = Annotated[float | None, BeforeValidator(Br.moeda)]
BrBool = Annotated[bool | None, BeforeValidator(Br.booleano)]


class _CaixaModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        ser_json_timedelta="iso8601",
    )


class CaixaItem(_CaixaModel):
    code: str
    state: str
    city: str
    neighborhood: str | None = None
    address: str | None = None
    price: BrMoney = None
    appraisal_value: BrMoney = None
    discount_pct: BrMoney = None
    financing: BrBool = None
    description: str | None = None
    modality: str
    link: str


class CaixaDetail(_CaixaModel):
    # Características
    property_type: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    parking_spaces: int | None = None
    total_area: float | None = None
    private_area: float | None = None
    land_area: float | None = None

    # Valores e datas de leilão
    minimum_sale_value: float | None = None
    first_auction_value: float | None = None
    second_auction_value: float | None = None
    first_auction_date: datetime | None = None
    second_auction_date: datetime | None = None

    # Licitação / documentação
    auctioneer: str | None = None
    notice: str | None = None
    item_number: str | None = None
    registration: str | None = None
    judicial_district: str | None = None
    registry_office: str | None = None
    municipal_registration: str | None = None
    postal_code: str | None = None
    full_address: str | None = None

    # Condições comerciais
    accepts_fgts: bool | None = None
    accepts_financing: bool | None = None
    payment_methods: list[str] = []
    condo_fees_on_buyer: bool | None = None
    taxes_on_buyer: bool | None = None
    occupancy_status: OccupancyStatus | None = None
    full_description: str | None = None

    # Documentos, localização e mídia
    notice_url: str | None = None
    registration_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    detail_status: DetailStatus = DetailStatus.OK
    photos: list[str] = []


class Analysis(_CaixaModel):
    discount_pct: float | None = None
    price_m2: float | None = None
    below_appraisal: bool | None = None


class AuctionRecord(_CaixaModel):
    item: CaixaItem
    detail: CaixaDetail | None = None
    analysis: Analysis | None = None
