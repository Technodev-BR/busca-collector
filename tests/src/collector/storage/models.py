from dataclasses import dataclass


@dataclass(slots=True)
class StorageFile:
    name: str
    content: bytes