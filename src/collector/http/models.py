from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class HttpRequest:
    method: str
    url: str
    params: dict[str, Any] | None = None
    json: Any | None = None
    data: Any | None = None
    headers: dict[str, str] | None = None
        

@dataclass(slots=True)
class HttpResponse:
    status_code: int
    url: str
    headers: dict[str, str]
    content: bytes
    
    @property
    def text(self) -> str:
        return self.content.decode(
            "utf-8",
            errors="ignore"
        )
    
    @property
    def is_sucess(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def content_type(self) -> dict[str, str]:
        return self.headers.get(
            "Content-Type",
            ""
        )        

@dataclass(slots=True)
class HttpOptions:
    timeout: int
    verify_tls: bool
    follow_redirects: bool
    proxy: str | None = None
    retry_attempts: int = 3
    retry_delay: int = 2