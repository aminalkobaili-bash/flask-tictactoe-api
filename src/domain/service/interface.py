from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.model.game import Game
from domain.model.field import GameField
from domain.model.game_type import GameType
from domain.model.leaderboard_entry import LeaderboardEntry
from domain.model.token_pair import TokenPair
from domain.model.user import User


class GameService(ABC):
    @abstractmethod
    def get_next_move(self, game: Game) -> tuple[int, int]:
        pass

    @abstractmethod
    def validate_field(self, game: Game, updated_field: GameField) -> None:
        pass

    @abstractmethod
    def is_game_over(self, game: Game) -> tuple[bool, int | None]:
        pass

    @abstractmethod
    def apply_computer_move(self, game: Game) -> Game:
        pass

    @abstractmethod
    def create_game(self, player_uuid: UUID, game_type: GameType) -> Game:
        pass

    @abstractmethod
    def join_game(self, game_uuid: UUID, player_uuid: UUID) -> Game:
        pass

    @abstractmethod
    def get_game(self, game_uuid: UUID) -> Game:
        pass

    @abstractmethod
    def make_move(
        self, game_uuid: UUID, player_uuid: UUID, new_field: GameField
    ) -> Game:
        pass

    @abstractmethod
    def list_waiting_games(self, user_uuid: UUID) -> list[Game]:
        pass

    @abstractmethod
    def list_finished_games(self, user_uuid: UUID) -> list[Game]:
        pass

    @abstractmethod
    def get_leaderboard(self, limit: int) -> list[LeaderboardEntry]:
        """
        Возвращает топ-N игроков по соотношению побед к поражениям и ничьим.
        """
        pass


class UserService(ABC):
    @abstractmethod
    def create_user(self, login: str, password: str) -> User:
        pass

    @abstractmethod
    def get_by_login(self, login: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_uuid(self, uuid: UUID) -> Optional[User]:
        pass


class AuthService(ABC):
    @abstractmethod
    def register(self, login: str, password: str) -> bool:
        pass

    @abstractmethod
    def authenticate(self, login: str, password: str) -> TokenPair:
        """Аутентифицирует пользователя и возвращает пару токенов."""
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """Обновляет access-токен, используя refresh-токен."""
        pass

    @abstractmethod
    def refresh_refresh_token(self, refresh_token: str) -> TokenPair:
        """Обновляет refresh-токен (и access-токен) по старому refresh-токену."""
        pass


class JwtProvider(ABC):
    @abstractmethod
    def generate_access_token(self, user_uuid: UUID) -> str:
        pass

    @abstractmethod
    def generate_refresh_token(self, user_uuid: UUID) -> str:
        pass

    @abstractmethod
    def validate_access_token(self, token: str) -> UUID:
        pass

    @abstractmethod
    def validate_refresh_token(self, token: str) -> UUID:
        pass
