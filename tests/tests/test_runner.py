from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from collector.core.enums import ErrorCode
from collector.core.exceptions import AppException, FonteIndisponivelError
from collector.core.runner import run


def test_run_sucesso_nao_sai():
    chamado = {"ok": False}

    def processo() -> None:
        chamado["ok"] = True

    run(processo)
    assert chamado["ok"] is True


def test_run_app_exception_usa_exit_code():
    def processo() -> None:
        raise FonteIndisponivelError("indispon?vel")

    with pytest.raises(SystemExit) as exc:
        run(processo)
    assert exc.value.code == ErrorCode.FONTE_INDISPONIVEL.exit_code


def test_run_validation_error_vira_config_invalido():
    class Modelo(BaseModel):
        x: int

    def processo() -> None:
        Modelo(x="nao-numero")  # type: ignore[arg-type]

    with pytest.raises(SystemExit) as exc:
        run(processo)
    assert exc.value.code == ErrorCode.CONFIG_INVALID.exit_code


def test_run_excecao_generica():
    def processo() -> None:
        raise ValueError("boom")

    with pytest.raises(SystemExit) as exc:
        run(processo)
    assert exc.value.code == ErrorCode.UNEXPECTED.exit_code


def test_app_exception_contexto_e_evento():
    exc = AppException("falhou", code=ErrorCode.BACKEND_ERRO, campos=["x"])
    assert exc.code is ErrorCode.BACKEND_ERRO
    assert exc.event == "backend.erro"
    assert exc.context == {"campos": ["x"]}


def test_app_exception_mensagem_padrao_do_codigo():
    exc = AppException(code=ErrorCode.CONFIG_INVALID)
    assert str(exc) == ErrorCode.CONFIG_INVALID.message


def test_error_code_metadados():
    assert ErrorCode.CONFIG_INVALID.event == "config.invalid"
    assert ErrorCode.CONFIG_INVALID.exit_code == 2
    assert ErrorCode.CONFIG_INVALID.message


def test_validation_error_direto():
    class Modelo(BaseModel):
        x: int

    with pytest.raises(ValidationError):
        Modelo(x="nao-numero")  # type: ignore[arg-type]
