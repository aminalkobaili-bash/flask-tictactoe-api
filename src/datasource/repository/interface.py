from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from datasource.orm.user import User
from domain.model.game import Game
from domain.model.leaderboard_entry import LeaderboardEntry


class GameRepository(ABC):
    @abstractmethod
    def save(self, game: Game) -> None:
        pass

    @abstractmethod
    def get(self, uuid: UUID) -> Game:
        pass

    @abstractmethod
    def exists(self, uuid: UUID) -> bool:
        pass

    @abstractmethod
    def list_waiting(self, exclude_player_uuid: Optional[UUID] = None) -> list[Game]:
        pass

    @abstractmethod
    def list_finished_by_user(self, user_uuid: UUID) -> list[Game]:
        pass

    @abstractmethod
    def get_leaderboard(self, limit: int) -> list[LeaderboardEntry]:
        """
        Возвращает топ-N игроков по соотношению побед к поражениям и ничьим.

        Args:
            limit: количество записей для возврата.

        Returns:
            Список LeaderboardEntry, отсортированный по убыванию win_ratio.
        """
        pass


class UserRepository(ABC):
    @abstractmethod
    def save(self, user: "User") -> None:
        pass

    @abstractmethod
    def get_by_login(self, login: str) -> Optional["User"]:
        pass

    @abstractmethod
    def get_by_uuid(self, uuid: UUID) -> Optional[User]:
        pass
