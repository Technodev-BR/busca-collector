from __future__ import annotations

from collector.core.enums import ErrorCode


class AppException(Exception):
    """Base de todas as exceções tratadas pelo handler global."""

    default_code: ErrorCode = ErrorCode.UNEXPECTED

    def __init__(
        self,
        message: str | None = None,
        *,
        code: ErrorCode | None = None,
        **context: object,
    ) -> None:
        self.code = code or type(self).default_code
        super().__init__(message or self.code.message)
        self.context = context

    @property
    def event(self) -> str:
        return self.code.event

    @property
    def exit_code(self) -> int:
        return self.code.exit_code


class HttpRetryException(AppException):
    """Falha transitória de rede/HTTP (429/5xx/transporte) — alvo do retry global."""

    default_code = ErrorCode.HTTP_TRANSITORIO


class AntiBotError(AppException):
    """A resposta é um desafio anti-bot/WAF, não o conteúdo esperado."""

    default_code = ErrorCode.FONTE_ANTIBOT


class LayoutInesperadoError(AppException):
    """Conteúdo da fonte em layout inesperado (CSV/HTML sem os campos esperados)."""

    default_code = ErrorCode.FONTE_LAYOUT


class FonteIndisponivelError(AppException):
    """Recurso indisponível na fonte (404 / 'imóvel não disponível')."""

    default_code = ErrorCode.FONTE_INDISPONIVEL


class ApiUnauthorizedException(AppException):
    """Backend recusou a requisição por falta de autorização (401)."""

    default_code = ErrorCode.BACKEND_CONEXAO


class ApiUnavailableException(AppException):
    """Backend indisponível (5xx) ao ingerir o registro."""

    default_code = ErrorCode.BACKEND_CONEXAO


class ApiValidationException(AppException):
    """Erro do backend ao ingerir um registro (resposta 4xx)."""

    default_code = ErrorCode.BACKEND_ERRO
