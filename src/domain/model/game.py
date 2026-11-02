from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from domain.model.field import GameField
from domain.model.game_status import GameStatus
from domain.model.game_type import GameType


@dataclass
class Game:
    uuid: UUID
    field: GameField
    created_at: datetime
    player1_uuid: Optional[UUID] = None
    player2_uuid: Optional[UUID] = None
    status: GameStatus = GameStatus.WAITING
    current_turn_uuid: Optional[UUID] = None
    winner_uuid: Optional[UUID] = None
    player1_symbol: int = 1
    player2_symbol: int = 2
    game_type: GameType = GameType.COMPUTER

    def __post_init__(self):
        if self.status == GameStatus.IN_PROGRESS and self.current_turn_uuid is None:
            raise ValueError("current_turn_uuid must be set when status is IN_PROGRESS")

    @classmethod
    def create_new(cls):
        return cls(uuid=uuid4(), field=GameField.empty(), created_at=datetime.now(timezone.utc))
