from __future__ import annotations

from datetime import date, datetime

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


class DetalheImovel(ApiModel):
    """Payload de enriquecimento enviado a POST /internal/ingest/imoveis/{codigo}/detalhe."""

    valor_primeiro_leilao: float | None = None
    valor_segundo_leilao: float | None = None
    data_primeiro_leilao: datetime | None = None
    data_segundo_leilao: datetime | None = None
    leiloeiro: str | None = None
    edital: str | None = None
    numero_item: str | None = None
    matricula: str | None = None
    comarca: str | None = None
    oficio: str | None = None
    inscricao_imobiliaria: str | None = None
    cep: str | None = None
    endereco_completo: str | None = None
    aceita_fgts: bool | None = None
    aceita_financiamento: bool | None = None
    despesas_condominio_comprador: bool | None = None
    despesas_tributos_comprador: bool | None = None
    situacao_ocupacao: str | None = None
    descricao_completa: str | None = None
    edital_url: str | None = None
    matricula_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status_enriquecimento: str = "ok"
    fotos: list[str] = []
