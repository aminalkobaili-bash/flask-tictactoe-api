from dataclasses import dataclass
from uuid import UUID


@dataclass
class LeaderboardEntry:
    user_uuid: UUID
    login: str
    win_ratio: float
