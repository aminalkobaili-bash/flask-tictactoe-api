from dataclasses import dataclass
from uuid import UUID


@dataclass
class User:
    uuid: UUID
    login: str
    password: str
