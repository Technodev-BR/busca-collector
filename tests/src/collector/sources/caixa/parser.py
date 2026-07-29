from __future__ import annotations

import csv
import io
import re
import unicodedata
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from collector.core.constants import CaixaConstants
from collector.core.enums import OccupancyStatus
from collector.core.exceptions import LayoutInesperadoError
from collector.core.logging import get_logger
from collector.core.parsing import Br
from collector.sources.caixa.models import AuctionRecord, CaixaDetail, CaixaItem
from collector.storage.models import StorageFile

# Palavras-chave (sem acento, minúsculas) que identificam cada coluna lógica no cabeçalho.
_COLUNAS = {
    "code": ("imovel", "numero do imovel"),
    "state": ("uf",),
    "city": ("cidade",),
    "neighborhood": ("bairro",),
    "address": ("endereco",),
    "price": ("preco",),
    "appraisal_value": ("avaliacao",),
    "discount_pct": ("desconto",),
    "financing": ("financ",),
    "description": ("descricao",),
    "modality": ("modalidade",),
    "link": ("link",),
}


class BaseParser:
    def _sem_acento(self, texto: str) -> str:
        return "".join(
            c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
        )


class CaixaParser(BaseParser):
    def __init__(self) -> None:
        self.__logger = get_logger(__name__)

    def parse(self, files: list[StorageFile]) -> list[AuctionRecord]:
        records: list[AuctionRecord] = []
        for file in files:
            uf = file.name.rsplit(".", 1)[0].upper()
            for item in self._parse_file(file.content, uf):
                records.append(AuctionRecord(item=item))
        return records

    def _parse_file(self, content: bytes, uf: str) -> list[CaixaItem]:
        registros = self._ler_csv(content)
        if not registros:
            self.__logger.warning("caixa.csv_vazio", uf=uf)
            return []

        colunas = self._resolver_colunas(list(registros[0].keys()))
        if not colunas.get("code"):
            raise ValueError(
                "Cabeçalho do CSV não reconhecido (coluna de código ausente). "
                "Provável bloqueio anti-bot da Caixa ou mudança de layout. "
                f"Colunas recebidas: {list(registros[0].keys())[:8]}"
            )

        items: list[CaixaItem] = []
        for registro in registros:
            item = self._mapear(registro, colunas, uf)
            if item is not None:
                items.append(item)
        return items

    # ---------- leitura do CSV ----------

    def _ler_csv(self, content: bytes) -> list[dict[str, str]]:
        texto: str | None = None
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                texto = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if texto is None:
            texto = content.decode("latin-1", errors="ignore")
        linhas = texto.splitlines()

        idx = self._localizar_cabecalho(linhas)
        if idx is None:
            return []

        corpo = "\n".join(linhas[idx:])
        leitor = csv.DictReader(io.StringIO(corpo), delimiter=";")

        registros: list[dict[str, str]] = []
        for linha in leitor:
            limpa = {
                k.strip(): (v.strip() if isinstance(v, str) else v)
                for k, v in linha.items()
                if k
            }
            if any(limpa.values()):
                registros.append(limpa)
        return registros

    def _localizar_cabecalho(self, linhas: list[str]) -> int | None:
        for i, linha in enumerate(linhas):
            if ";" not in linha:
                continue
            celulas = [self._sem_acento(c.strip().lower()) for c in linha.split(";")]
            if any("imovel" in c for c in celulas) and any(c == "uf" for c in celulas):
                return i
        return None

    # ---------- mapeamento de colunas e campos ----------

    def _resolver_colunas(self, cabecalho: list[str]) -> dict[str, str | None]:
        """Mapeia chave lógica -> nome real da coluna no CSV (ou ``None`` se ausente)."""
        normalizado = {col: self._sem_acento(col.strip().lower()) for col in cabecalho}
        resultado: dict[str, str | None] = {}
        for chave, palavras in _COLUNAS.items():
            resultado[chave] = next(
                (col for col, norm in normalizado.items() if any(p in norm for p in palavras)),
                None,
            )
        return resultado

    def _get(self, registro: dict[str, str], coluna: str | None) -> str | None:
        if not coluna:
            return None
        valor = registro.get(coluna)
        return valor.strip() if isinstance(valor, str) else valor

    def _mapear(
        self,
        registro: dict[str, str],
        colunas: dict[str, str | None],
        uf_default: str,
    ) -> CaixaItem | None:
        code = self._get(registro, colunas.get("code"))
        if not code:
            return None

        return CaixaItem(
            code=code,
            state=(self._get(registro, colunas.get("state")) or uf_default).upper(),
            city=self._get(registro, colunas.get("city")) or "",
            neighborhood=self._get(registro, colunas.get("neighborhood")),
            address=self._get(registro, colunas.get("address")),
            price=self._get(registro, colunas.get("price")),
            appraisal_value=self._get(registro, colunas.get("appraisal_value")),
            discount_pct=self._get(registro, colunas.get("discount_pct")),
            financing=self._get(registro, colunas.get("financing")),
            description=self._get(registro, colunas.get("description")),
            modality=self._get(registro, colunas.get("modality")) or "",
            link=self._get(registro, colunas.get("link")) or "",
        )


class CaixaDetailParser(BaseParser):
    """Converte o HTML da ficha do imóvel em ``CaixaDetail`` (parsing e tratativa de campos)."""

    # Campos vindos dos rótulos (Rótulo: valor): destino -> (chaves possíveis, conversor).
    _CAMPOS_ROTULO: dict[str, tuple[tuple[str, ...], Callable[[object], object]]] = {
        "property_type": (("tipo de imovel",), Br.texto),
        "bedrooms": (("quartos",), Br.inteiro),
        "bathrooms": (("banheiros",), Br.inteiro),
        "parking_spaces": (("vaga de garagem", "vagas", "garagem"), Br.inteiro),
        "total_area": (("area total",), Br.area),
        "private_area": (("area privativa",), Br.area),
        "land_area": (("area do terreno",), Br.area),
        "registration": (("matricula(s)", "matricula"), Br.texto),
        "judicial_district": (("comarca",), Br.texto),
        "registry_office": (("oficio",), Br.texto),
        "municipal_registration": (("inscricao imobiliaria",), Br.texto),
    }

    def is_unavailable(self, html: str) -> bool:
        baixo = html.lower()
        return (
            "imóvel não disponível" in baixo
            or "imovel nao disponivel" in baixo
            or "não está mais disponível" in baixo
        )

    def parse(self, html: str, code: str) -> CaixaDetail:
        soup = BeautifulSoup(html, "html.parser")
        raiz = soup.find(id="dadosImovel") or soup
        rotulos = self._coletar_rotulos(raiz)
        linhas = raiz.get_text(separator="\n").replace("\xa0", " ").splitlines()
        texto = "\n".join(ln.strip() for ln in linhas if ln.strip())
        formas = self._formas_pagamento(texto)

        dados = {
            campo: conv(self._primeiro_rotulo(rotulos, chaves))
            for campo, (chaves, conv) in self._CAMPOS_ROTULO.items()
        }

        detail = CaixaDetail(
            **dados,
            minimum_sale_value=self._valor_apos(texto, r"[Vv]alor m[íi]nimo de venda"),
            first_auction_value=(
                self._valor_apos(texto, r"1[ºo]\s*Leil[ãa]o")
                or self._valor_apos(texto, r"[Vv]alor m[íi]nimo de venda")
            ),
            second_auction_value=self._valor_apos(texto, r"2[ºo]\s*Leil[ãa]o"),
            first_auction_date=(
                self._data_apos(texto, r"[Dd]ata\s+d[ao]\s+1[ºo]\s*Leil[ãa]o")
                or self._data_apos(texto, r"[Dd]ata\s+d[ao]\s+Licita[çc][ãa]o")
            ),
            second_auction_date=self._data_apos(texto, r"[Dd]ata\s+d[ao]\s+2[ºo]\s*Leil[ãa]o"),
            auctioneer=self._texto_apos(texto, r"[Ll]eiloeiro\(?a?\)?"),
            notice=self._texto_apos(texto, r"[Ee]dital"),
            item_number=self._texto_apos(texto, r"N[úu]mero do item"),
            postal_code=self._cep(texto),
            full_address=self._texto_apos(texto, r"[Ee]ndere[çc]o"),
            full_description=self._texto_apos(texto, r"[Dd]escri[çc][ãa]o"),
            occupancy_status=self._ocupacao(texto),
            accepts_fgts="FGTS" in formas if formas else None,
            accepts_financing="Financiamento" in formas if formas else None,
            payment_methods=formas,
            notice_url=self._doc_url(soup, "edital"),
            registration_url=self._doc_url(soup, "matr"),
            photos=self._fotos(soup),
        )
        self._aplicar_despesas(detail, texto)

        if self._tudo_vazio(detail):
            raise LayoutInesperadoError(
                f"Nenhum campo extraído para {code} (possível mudança de layout)"
            )
        return detail

    def _primeiro_rotulo(self, rotulos: dict[str, str], chaves: tuple[str, ...]) -> str | None:
        for chave in chaves:
            valor = rotulos.get(chave)
            if valor:
                return valor
        return None

    # ---------- rótulos (Rótulo: <strong>valor</strong>) ----------

    def _coletar_rotulos(self, raiz: object) -> dict[str, str]:
        pares: dict[str, str] = {}
        for span in raiz.find_all("span"):  # type: ignore[attr-defined]
            strong = span.find("strong")
            if strong is None:
                continue
            valor = strong.get_text(strip=True)
            rotulo_bruto = span.get_text().replace(strong.get_text(), "", 1)
            limpo = rotulo_bruto.replace("\xa0", " ").strip().rstrip(":= ").strip().lower()
            rotulo = self._sem_acento(limpo)
            if rotulo and valor:
                pares.setdefault(rotulo, valor)
        return pares

    # ---------- extração por rótulo no texto ----------

    def _texto_apos(self, texto: str, rotulo: str) -> str | None:
        m = re.search(rotulo + r"\s*[:\-]?\s*(.*)", texto)
        if not m:
            return None
        valor = m.group(1).strip()
        if not valor:
            resto = texto[m.end():].lstrip("\n")
            valor = resto.split("\n", 1)[0].strip() if resto else ""
        valor = valor.strip(" .:-")
        return valor[:300] if valor else None

    def _valor_apos(self, texto: str, rotulo: str) -> float | None:
        m = re.search(
            rotulo + r".{0,60}?" + CaixaConstants.MONEY_PATTERN.pattern, texto, re.DOTALL
        )
        return Br.numero(m.group(1)) if m else None

    def _data_apos(self, texto: str, rotulo: str) -> datetime | None:
        m = re.search(
            rotulo + r".{0,40}?" + CaixaConstants.DATE_PATTERN.pattern, texto, re.DOTALL
        )
        if not m:
            return None
        dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hora = int(m.group(4)) if m.group(4) else 0
        minuto = int(m.group(5)) if m.group(5) else 0
        try:
            # horário local BR -> UTC (aproximação por offset fixo de -3h)
            local = datetime(ano, mes, dia, hora, minuto)
            return (local + timedelta(hours=CaixaConstants.BR_UTC_OFFSET_HOURS)).replace(
                tzinfo=UTC
            )
        except ValueError:
            return None

    def _cep(self, texto: str) -> str | None:
        m = CaixaConstants.CEP_PATTERN.search(texto)
        return m.group(1) if m else None

    def _ocupacao(self, texto: str) -> OccupancyStatus | None:
        baixo = texto.lower()
        if "desocupado" in baixo:
            return OccupancyStatus.UNOCCUPIED
        if "ocupado" in baixo:
            return OccupancyStatus.OCCUPIED
        return None

    def _formas_pagamento(self, texto: str) -> list[str]:
        baixo = self._sem_acento(texto.lower())
        ini = baixo.find("formas de pagamento")
        if ini < 0:
            return []
        fim = baixo.find("regras para pagamento", ini)
        bloco = baixo[ini : fim if fim > 0 else ini + 400]

        formas: list[str] = []
        if "recursos proprios" in bloco or "a vista" in bloco:
            formas.append("Recursos próprios")
        if "fgts" in bloco:
            formas.append("FGTS")
        if "financ" in bloco and "nao permite financ" not in bloco:
            formas.append("Financiamento")
        if "consorcio" in bloco:
            formas.append("Consórcio")
        if "parcelamento" in bloco:
            formas.append("Parcelamento")
        return formas

    def _aplicar_despesas(self, detail: CaixaDetail, texto: str) -> None:
        baixo = self._sem_acento(texto.lower())
        if "condom" in baixo:
            detail.condo_fees_on_buyer = self._por_conta_comprador(baixo, "condom")
        if "tributo" in baixo:
            detail.taxes_on_buyer = self._por_conta_comprador(baixo, "tributo")

    def _por_conta_comprador(self, texto: str, chave: str) -> bool:
        idx = texto.find(chave)
        if idx < 0:
            return False
        return "comprador" in texto[idx : idx + 120]

    # ---------- documentos e fotos ----------

    def _doc_url(self, soup: BeautifulSoup, termo: str) -> str | None:
        termo = termo.lower()
        for a in soup.find_all("a", onclick=True):
            m = CaixaConstants.EXIBEDOC_PATTERN.search(str(a.get("onclick", "")))
            if not m:
                continue
            caminho = m.group(1)
            texto_link = self._sem_acento(a.get_text(strip=True).lower())
            if termo in texto_link or termo in caminho.lower():
                return urljoin(CaixaConstants.BASE_URL, caminho)
        return None

    def _fotos(self, soup: BeautifulSoup) -> list[str]:
        urls: list[str] = []
        galeria = soup.find(id="galeria-imagens") or soup
        for img in galeria.find_all("img", src=True):  # type: ignore[union-attr]
            full = urljoin(CaixaConstants.BASE_URL, str(img["src"]))
            if full not in urls:
                urls.append(full)
        return urls

    def _tudo_vazio(self, detail: CaixaDetail) -> bool:
        dados = detail.model_dump(exclude={"detail_status", "photos", "payment_methods"})
        return (
            all(v is None for v in dados.values())
            and not detail.photos
            and not detail.payment_methods
        )
