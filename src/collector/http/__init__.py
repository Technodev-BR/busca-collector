from __future__ import annotations

from collector.core.settings import Settings
from collector.http.client import HttpClient
from collector.http.http import Http
from collector.http.models import HttpOptions
from collector.http.session import HttpSession


def configure_http(settings: Settings) -> Http:
    options = HttpOptions(
        timeout=int(settings.request_timeout),
        verify_tls=settings.verify_tls,
        follow_redirects=True,
        proxy=settings.https_proxy,
    )
    session = HttpSession(
        application="busca-collector",
        user_agent=settings.user_agent_base,
        accept="*/*",
        accept_language="pt-BR,pt;q=0.9",
        referer="",
    )
    return HttpClient(options, session)


__all__ = ["Http", "HttpClient", "configure_http"]
