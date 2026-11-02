from typing import Optional
from uuid import UUID, uuid4

from domain.exceptions import (
    DomainError,
    GameNotWaitingError,
    InvalidMoveError,
    GameOverError,
    WrongPlayerTurnError,
)
from domain.model.field import GameField
from domain.model.game import Game
from domain.model.game_status import GameStatus
from domain.model.game_type import GameType
from domain.model.leaderboard_entry import LeaderboardEntry
from domain.model.user import User
from domain.service.interface import AuthService, GameService, JwtProvider, UserService
from datasource.repository.interface import GameRepository, UserRepository
from datasource.repository.exceptions import DuplicateRepositoryError
from domain.model.token_pair import TokenPair
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone


class GameServiceImpl(GameService):
    def __init__(self, repository: GameRepository):
        self.repository = repository

    def _validate_move(self, game: Game, new_field: GameField) -> None:
        if game.status != GameStatus.IN_PROGRESS:
            raise GameOverError("Game is already over")
        old = game.field.matrix
        new = new_field.matrix
        if game.current_turn_uuid == game.player1_uuid:
            expected_symbol = game.player1_symbol
        elif game.current_turn_uuid == game.player2_uuid:
            expected_symbol = game.player2_symbol
        else:
            raise InvalidMoveError(
                "Invalid turn state: current turn is not a human player"
            )
        changes = 0
        for r in range(3):
            for c in range(3):
                if old[r][c] != new[r][c]:
                    if old[r][c] != 0 or new[r][c] != expected_symbol:
                        raise InvalidMoveError(f"Invalid change at ({r},{c})")
                    changes += 1
        if changes != 1:
            raise InvalidMoveError("Exactly one move required")

    def _determine_status(self, game: Game) -> tuple[GameStatus, Optional[UUID]]:
        field = game.field.matrix
        lines = []
        lines.extend(field)
        for col in range(3):
            lines.append([field[0][col], field[1][col], field[2][col]])
        lines.append([field[0][0], field[1][1], field[2][2]])
        lines.append([field[0][2], field[1][1], field[2][0]])

        for line in lines:
            if line[0] != 0 and len(set(line)) == 1:
                winner_symbol = line[0]
                if winner_symbol == game.player1_symbol:
                    winner_uuid = game.player1_uuid
                elif winner_symbol == game.player2_symbol:
                    winner_uuid = game.player2_uuid  # может быть None для компьютера
                else:
                    winner_uuid = None
                return GameStatus.WON, winner_uuid

        if game.field.is_full():
            return GameStatus.DRAW, None

        return GameStatus.IN_PROGRESS, None

    def _switch_turn(self, game: Game) -> None:
        if game.game_type != GameType.HUMAN:
            raise DomainError("Cannot switch turn in non-human game")
        if game.current_turn_uuid == game.player1_uuid:
            game.current_turn_uuid = game.player2_uuid
        elif game.current_turn_uuid == game.player2_uuid:
            game.current_turn_uuid = game.player1_uuid
        else:
            raise DomainError("Invalid turn state")

    def _apply_computer_move(self, game: Game) -> None:
        if game.game_type != GameType.COMPUTER:
            raise DomainError("Cannot apply computer move for non-computer game")
        if game.status != GameStatus.IN_PROGRESS:
            raise GameOverError("Game is not in progress")
        row, col = self.get_next_move(game)
        new_matrix = [list(r) for r in game.field.matrix]
        new_matrix[row][col] = game.player2_symbol
        game.field = GameField(matrix=new_matrix)
        status, winner_uuid = self._determine_status(game)
        game.status = status
        game.winner_uuid = winner_uuid
        if status == GameStatus.IN_PROGRESS:
            game.current_turn_uuid = game.player1_uuid
        else:
            game.current_turn_uuid = None

    def get_next_move(self, game: Game) -> tuple[int, int]:
        finished, _ = self.is_game_over(game)
        if finished:
            raise GameOverError("Game is already over")
        empty = game.field.get_empty_cells()
        if not empty:
            raise GameOverError("No empty cells")
        best_score = -float("inf")
        best_move = empty[0]
        for row, col in empty:
            new_matrix = [list(r) for r in game.field.matrix]
            new_matrix[row][col] = 2
            new_field = GameField(matrix=tuple(tuple(r) for r in new_matrix))
            score = self._minimax(new_field, depth=0, is_maximizing=False)
            if score > best_score:
                best_score = score
                best_move = (row, col)
        return best_move

    def _minimax(self, field: GameField, depth: int, is_maximizing: bool) -> int:
        temp_game = Game(
            uuid=uuid4(),
            field=field,
            created_at=datetime.now(timezone.utc),
            player1_uuid=uuid4(),
            player2_uuid=uuid4(),
            status=GameStatus.IN_PROGRESS,
            current_turn_uuid=uuid4(),
            player1_symbol=1,
            player2_symbol=2,
            game_type=GameType.COMPUTER,
        )
        finished, winner = self.is_game_over(temp_game)
        if finished:
            if winner == 2:
                return 10 - depth
            elif winner == 1:
                return -10 + depth
            else:
                return 0
        empty = field.get_empty_cells()
        if not empty:
            return 0
        if is_maximizing:
            best = -float("inf")
            for row, col in empty:
                new_matrix = [list(row) for row in field.matrix]
                new_matrix[row][col] = 2
                new_field = GameField(matrix=new_matrix)
                score = self._minimax(new_field, depth + 1, False)
                best = max(best, score)
            return best
        else:
            best = float("inf")
            for row, col in empty:
                new_matrix = [list(row) for row in field.matrix]
                new_matrix[row][col] = 1
                new_field = GameField(matrix=new_matrix)
                score = self._minimax(new_field, depth + 1, True)
                best = min(best, score)
            return best

    def validate_field(self, game: Game, updated_field: GameField) -> None:
        self._validate_move(game, updated_field)

    def is_game_over(self, game: Game) -> tuple[bool, int | None]:
        status, winner_uuid = self._determine_status(game)
        if status == GameStatus.WON:
            if winner_uuid == game.player1_uuid:
                return True, game.player1_symbol
            elif winner_uuid == game.player2_uuid:
                return True, game.player2_symbol
            else:
                return True, None  # победитель-компьютер
        elif status == GameStatus.DRAW:
            return True, None
        else:
            return False, None

    def apply_computer_move(self, game: Game) -> Game:
        self._apply_computer_move(game)
        return game

    def create_game(self, player_uuid: UUID, game_type: GameType) -> Game:
        if game_type == GameType.COMPUTER:
            status = GameStatus.IN_PROGRESS
            current_turn = player_uuid
        else:
            status = GameStatus.WAITING
            current_turn = None
        game = Game(
            uuid=uuid4(),
            field=GameField.empty(),
            created_at=datetime.now(timezone.utc),
            player1_uuid=player_uuid,
            player2_uuid=None,
            status=status,
            current_turn_uuid=current_turn,
            winner_uuid=None,
            player1_symbol=1,
            player2_symbol=2,
            game_type=game_type,
        )
        self.repository.save(game)
        return game

    def join_game(self, game_uuid: UUID, player_uuid: UUID) -> Game:
        game = self.repository.get(game_uuid)
        if game.game_type != GameType.HUMAN:
            raise DomainError("Cannot join computer game")
        if game.status != GameStatus.WAITING:
            raise GameNotWaitingError("Game is not waiting for players")
        if game.player1_uuid == player_uuid:
            raise DomainError("Player is already in this game")
        if game.player2_uuid is not None:
            raise DomainError("Game already has a second player")
        game.player2_uuid = player_uuid
        game.status = GameStatus.IN_PROGRESS
        game.current_turn_uuid = game.player1_uuid
        self.repository.save(game)
        return game

    def get_game(self, game_uuid: UUID) -> Game:
        return self.repository.get(game_uuid)

    def make_move(
        self, game_uuid: UUID, player_uuid: UUID, new_field: GameField
    ) -> Game:
        game = self.repository.get(game_uuid)
        if game.status != GameStatus.IN_PROGRESS:
            raise GameOverError("Game is not in progress")
        if game.current_turn_uuid != player_uuid:
            raise WrongPlayerTurnError("It's not your turn")

        # Валидация хода (не изменяет game)
        self._validate_move(game, new_field)

        # Применяем ход игрока
        game.field = new_field
        status, winner_uuid = self._determine_status(game)
        game.status = status
        game.winner_uuid = winner_uuid

        if status != GameStatus.IN_PROGRESS:
            game.current_turn_uuid = None
            self.repository.save(game)
            return game

        if game.game_type == GameType.HUMAN:
            self._switch_turn(game)
        else:
            self._apply_computer_move(game)
            if game.status == GameStatus.IN_PROGRESS:
                game.current_turn_uuid = game.player1_uuid
            else:
                game.current_turn_uuid = None

        self.repository.save(game)
        return game

    def list_waiting_games(self, user_uuid: UUID) -> list[Game]:
        return self.repository.list_waiting(exclude_player_uuid=user_uuid)

    def list_finished_games(self, user_uuid: UUID) -> list[Game]:
        return self.repository.list_finished_by_user(user_uuid)

    def get_leaderboard(self, limit: int) -> list[LeaderboardEntry]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        return self.repository.get_leaderboard(limit)


class UserServiceImpl(UserService):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, login: str, password: str) -> User:
        if self.user_repository.get_by_login(login) is not None:
            raise DomainError("User with this login already exists")
        user = User(uuid=uuid4(), login=login, password=generate_password_hash(password))
        try:
            self.user_repository.save(user)
        except DuplicateRepositoryError:
            raise DomainError("User with this login already exists")
        return user

    def get_by_login(self, login: str) -> Optional[User]:
        return self.user_repository.get_by_login(login)

    def get_by_uuid(self, uuid: UUID) -> Optional[User]:
        return self.user_repository.get_by_uuid(uuid)


class AuthServiceImpl(AuthService):
    def __init__(self, user_service: UserService, jwt_provider: JwtProvider):
        self.user_service = user_service
        self.jwt_provider = jwt_provider

    def register(self, login: str, password: str) -> bool:
        self.user_service.create_user(login, password)
        return True

    def authenticate(self, login: str, password: str) -> TokenPair:
        user = self.user_service.get_by_login(login)
        if user is None or not check_password_hash(user.password, password):
            raise DomainError("Invalid login or password")
        access_token = self.jwt_provider.generate_access_token(user.uuid)
        refresh_token = self.jwt_provider.generate_refresh_token(user.uuid)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def refresh_access_token(self, refresh_token: str) -> TokenPair:
        user_uuid = self.jwt_provider.validate_refresh_token(refresh_token)
        new_access_token = self.jwt_provider.generate_access_token(user_uuid)
        # refresh-токен остаётся старым (не меняем)
        return TokenPair(access_token=new_access_token, refresh_token=refresh_token)

    def refresh_refresh_token(self, refresh_token: str) -> TokenPair:
        user_uuid = self.jwt_provider.validate_refresh_token(refresh_token)
        new_access_token = self.jwt_provider.generate_access_token(user_uuid)
        new_refresh_token = self.jwt_provider.generate_refresh_token(user_uuid)
        return TokenPair(access_token=new_access_token, refresh_token=new_refresh_token)
