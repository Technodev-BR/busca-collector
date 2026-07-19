from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        ser_json_timedelta="iso8601",
    )


class ImovelColetado(ApiModel):
    codigo: str
    uf: str
    cidade: str
    bairro: str | None = None
    endereco: str | None = None
    preco: float | None = None
    valor_avaliacao: float | None = None
    desconto_pct: float | None = None
    financiamento: bool | None = None
    descricao: str | None = None
    modalidade: str
    link: str


class LoteImoveis(ApiModel):
    fonte: str
    uf: str
    gerado_em: date
    imoveis: list[ImovelColetado]
