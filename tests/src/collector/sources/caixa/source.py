from __future__ import annotations

from collector.core.constants import CaixaConstants
from collector.core.exceptions import AntiBotError
from collector.core.logging import get_logger
from collector.core.settings import Settings
from collector.http.http import Http
from collector.sources.caixa.analysis import CaixaAnalysis
from collector.sources.caixa.enricher import CaixaEnricher
from collector.sources.caixa.models import AuctionRecord
from collector.sources.caixa.parser import CaixaParser
from collector.sources.source import Source
from collector.storage.models import StorageFile
from collector.storage.storage import Storage


class CaixaSource(Source):
    def __init__(
        self,
        http: Http,
        storage: Storage,
        settings: Settings,
        parser: CaixaParser,
        enricher: CaixaEnricher,
        analysis: CaixaAnalysis,
    ) -> None:
        self.__logger = get_logger(__name__)
        self.__http = http
        self.__storage = storage
        self.__settings = settings
        self.__parser = parser
        self.__enricher = enricher
        self.__analysis = analysis

    def collect(self) -> list[AuctionRecord]:
        self.__logger.info("caixa.collect.start", local_run=self.__settings.local_run)

        files = self._download_files()
        records = self.__parser.parse(files)
        records = self.__enricher.process(records)
        records = self.__analysis.process(records)

        self.__logger.info("caixa.collect.finished", records=len(records))
        return records

    def _download_files(self) -> list[StorageFile]:
        if self.__settings.local_run:
            return self.__storage.read(CaixaConstants.DOWNLOAD_DIR)

        files: list[StorageFile] = []
        for uf in CaixaConstants.UFS_BR:
            content = self._download_uf(uf)
            if content is None:
                continue
            files.append(StorageFile(name=CaixaConstants.FILE_NAME.format(uf=uf), content=content))

        if files:
            self.__storage.save(CaixaConstants.DOWNLOAD_DIR, files)
        return files

    def _download_uf(self, uf: str) -> bytes | None:
        url = self.__settings.csv_url_template.format(uf=uf)
        resp = self.__http.get(url, headers={"Accept": CaixaConstants.CSV_ACCEPT})

        if resp.status_code == 404:
            self.__logger.warning("caixa.csv_404", uf=uf)
            return None
        if not (200 <= resp.status_code < 300):
            self.__logger.warning("caixa.csv_status", uf=uf, status=resp.status_code)
            return None

        content = resp.content
        amostra = content[:512].lower()
        if b"<html" in amostra and b";" not in amostra:
            raise AntiBotError(f"Resposta anti-bot/WAF ao baixar CSV da UF {uf}")
        return content
