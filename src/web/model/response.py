from uuid import UUID
from typing import List, Optional
from domain.model.game_status import GameStatus
from domain.model.game_type import GameType


class GameResponse:
    def __init__(
        self,
        uuid: UUID,
        field: List[List[int]],
        status: GameStatus,
        player1_uuid: Optional[UUID],
        player2_uuid: Optional[UUID],
        current_turn_uuid: Optional[UUID],
        winner_uuid: Optional[UUID],
        game_type: GameType,
    ):
        self.uuid = uuid
        self.field = field
        self.status = status.value
        self.player1_uuid = str(player1_uuid) if player1_uuid else None
        self.player2_uuid = str(player2_uuid) if player2_uuid else None
        self.current_turn_uuid = str(current_turn_uuid) if current_turn_uuid else None
        self.winner_uuid = str(winner_uuid) if winner_uuid else None
        self.game_type = game_type.value

    def to_json(self) -> dict:
        return {
            "uuid": str(self.uuid),
            "field": self.field,
            "status": self.status,
            "player1_uuid": self.player1_uuid,
            "player2_uuid": self.player2_uuid,
            "current_turn_uuid": self.current_turn_uuid,
            "winner_uuid": self.winner_uuid,
            "game_type": self.game_type,
        }


class UserResponse:
    def __init__(self, uuid: UUID, login: str):
        self.uuid = uuid
        self.login = login

    def to_json(self) -> dict:
        return {"uuid": str(self.uuid), "login": self.login}


class JwtResponse:
    def __init__(self, access_token: str, refresh_token: str):
        self.type = "Bearer"
        self.access_token = access_token
        self.refresh_token = refresh_token

    def to_json(self) -> dict:
        return {
            "type": self.type,
            "accessToken": self.access_token,
            "refreshToken": self.refresh_token,
        }
