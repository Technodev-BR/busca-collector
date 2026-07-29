from __future__ import annotations

import sys
from collections.abc import Callable

from pydantic import ValidationError

from collector.core.enums import ErrorCode
from collector.core.exceptions import AppException
from collector.core.logging import get_logger

logger = get_logger(__name__)


def run(process: Callable[[], object]) -> None:
    logger.info("app.iniciando")
    try:
        process()
    except AppException as ex:
        logger.error(ex.event, error=str(ex), code=ex.code.name, **ex.context)
        sys.exit(ex.exit_code)
    except ValidationError as ex:
        code = ErrorCode.CONFIG_INVALID
        logger.error(code.event, error=str(ex), code=code.name)
        sys.exit(code.exit_code)
    except Exception as ex:  # noqa: BLE001 - fronteira do processo
        code = ErrorCode.UNEXPECTED
        logger.exception(code.event, error=str(ex), type=type(ex).__name__)
        sys.exit(code.exit_code)
    finally:
        logger.info("app.finalizado")
