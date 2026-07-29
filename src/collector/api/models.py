from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class ApiRecord:
    key: str
    payload: dict[str, Any]
