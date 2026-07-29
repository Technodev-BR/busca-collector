from __future__ import annotations

import hashlib
import time
from datetime import timedelta

from collector.cache.cache import Cache
from collector.core.constants import CaixaConstants
from collector.core.exceptions import FonteIndisponivelError
from collector.core.logging import get_logger
from collector.core.settings import Settings
from collector.http.http import Http
from collector.sources.caixa.models import AuctionRecord, CaixaItem
from collector.sources.caixa.parser import CaixaDetailParser


class CaixaEnricher:
    def __init__(self, settings: Settings, http: Http, cache: Cache) -> None:
        self.__logger = get_logger(__name__)
        self.__settings = settings
        self.__http = http
        self.__cache = cache
        self.__parser = CaixaDetailParser()

    def process(self, records: list[AuctionRecord]) -> list[AuctionRecord]:
        if not self.__settings.detalhar_inline:
            return records

        limite = self.__settings.detalhe_limite
        processados = 0
        for record in records:
            if limite and processados >= limite:
                break

            item = record.item
            fingerprint = self._fingerprint(item)
            if not self._deve_detalhar(item.state, item.code, fingerprint):
                continue

            processados += 1
            code = item.code
            url = self.__settings.detalhe_url_template.format(codigo=code)
            try:
                resp = self.__http.get(url, headers={"Accept": CaixaConstants.DETAIL_ACCEPT})
                if resp.status_code == 404:
                    raise FonteIndisponivelError(f"Detalhe 404 para {code}")
                if not (200 <= resp.status_code < 300):
                    raise FonteIndisponivelError(f"Detalhe status {resp.status_code} para {code}")
                if self.__parser.is_unavailable(resp.text):
                    raise FonteIndisponivelError(f"Página de indisponível para {code}")
                record.detail = self.__parser.parse(resp.text, code)
            except FonteIndisponivelError:
                record.detail = None
                self._registrar(item.state, code, fingerprint)
            except Exception as ex:  # noqa: BLE001 - falha isolada não deve abortar a coleta
                record.detail = None
                self.__logger.warning("caixa.detalhe_falhou", codigo=code, error=str(ex))
            else:
                self._registrar(item.state, code, fingerprint)

            if self.__settings.detalhe_pausa_seg:
                time.sleep(self.__settings.detalhe_pausa_seg)

        self.__logger.info("caixa.enricher.finished", detalhados=processados)
        return records

    # ---------- cache (fingerprint) ----------

    def _cache_key(self, uf: str, code: str) -> str:
        return f"caixa:detail:{uf}:{code}"

    def _deve_detalhar(self, uf: str, code: str, fingerprint: str) -> bool:
        return self.__cache.get(self._cache_key(uf, code)) != fingerprint

    def _registrar(self, uf: str, code: str, fingerprint: str) -> None:
        ttl = timedelta(days=self.__settings.redis_ttl_dias)
        self.__cache.set(self._cache_key(uf, code), fingerprint, ttl=ttl)

    def _fingerprint(self, item: CaixaItem) -> str:
        """Fingerprint estável dos campos que, ao mudarem, exigem re-buscar o detalhe."""
        base = f"{item.price}|{item.appraisal_value}|{item.modality}|{item.link}"
        return hashlib.sha1(base.encode("utf-8")).hexdigest()
