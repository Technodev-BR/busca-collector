from __future__ import annotations

from enum import Enum, StrEnum


class ErrorCode(Enum):
    CONFIG_INVALID = (
        "config.invalid",
        2,
        "Configuração inválida. Copie .env.example para .env ou defina as variáveis COLLECTOR_*.",
    )
    HTTP_TRANSITORIO = (
        "http.transitorio",
        1,
        "Falha transitória de rede/HTTP após múltiplas tentativas.",
    )
    FONTE_ANTIBOT = ("fonte.antibot", 1, "Bloqueio anti-bot/WAF ao acessar a fonte.")
    FONTE_LAYOUT = ("fonte.layout", 1, "Conteúdo da fonte em layout inesperado.")
    FONTE_INDISPONIVEL = ("fonte.indisponivel", 1, "Recurso indisponível na fonte.")
    BACKEND_CONEXAO = ("backend.conexao", 1, "Falha de conexão com o backend.")
    BACKEND_ERRO = ("backend.erro", 1, "Erro do backend ao ingerir o registro.")
    UNEXPECTED = ("unexpected.error", 1, "Falha inesperada.")

    def __init__(self, event: str, exit_code: int, message: str) -> None:
        self.event = event
        self.exit_code = exit_code
        self.message = message


class StorageDirectory(StrEnum):
    CAIXA_DOWNLOAD = "downloads/caixa"


class DetailStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class OccupancyStatus(StrEnum):
    OCCUPIED = "occupied"
    UNOCCUPIED = "unoccupied"
