from uuid import UUID
from datasource.orm.game import Game as ORMGame
from domain.model.game import Game
from domain.exceptions import GameNotFoundError
from datasource.repository.interface import GameRepository
from domain.model.game_status import GameStatus
from datasource.mapper import game_to_domain, game_to_orm
from domain.model.leaderboard_entry import LeaderboardEntry
from sqlalchemy import Float, and_, case, cast, func, or_, select
from sqlalchemy.orm import aliased
from datasource.orm.user import User as ORMUser


class PostgresGameRepository(GameRepository):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save(self, game: Game) -> None:
        session = self.session_factory()
        try:
            orm_game = session.query(ORMGame).filter(ORMGame.uuid == game.uuid).first()
            if orm_game:
                orm_game.field_matrix = game.field.matrix
                orm_game.player1_uuid = game.player1_uuid
                orm_game.player2_uuid = game.player2_uuid
                orm_game.status = game.status
                orm_game.current_turn_uuid = game.current_turn_uuid
                orm_game.winner_uuid = game.winner_uuid
                orm_game.player1_symbol = game.player1_symbol
                orm_game.player2_symbol = game.player2_symbol
                orm_game.game_type = game.game_type
            else:
                new_orm = game_to_orm(game)
                session.add(new_orm)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get(self, uuid: UUID) -> Game:
        session = self.session_factory()
        try:
            orm_game = session.query(ORMGame).filter(ORMGame.uuid == uuid).first()
            if orm_game is None:
                raise GameNotFoundError(f"Game {uuid} not found")
            return game_to_domain(orm_game)
        finally:
            session.close()

    def exists(self, uuid: UUID) -> bool:
        session = self.session_factory()
        try:
            return (
                session.query(ORMGame).filter(ORMGame.uuid == uuid).first() is not None
            )
        finally:
            session.close()

    def list_waiting(self, exclude_player_uuid: UUID | None = None) -> list[Game]:
        session = self.session_factory()
        try:
            query = session.query(ORMGame).filter(ORMGame.status == GameStatus.WAITING)
            if exclude_player_uuid is not None:
                query = query.filter(ORMGame.player1_uuid != exclude_player_uuid)
            orm_games = query.all()
            return [game_to_domain(orm) for orm in orm_games]
        finally:
            session.close()

    def list_finished_by_user(self, user_uuid: UUID) -> list[Game]:
        session = self.session_factory()
        try:
            query = session.query(ORMGame).filter(
                (ORMGame.player1_uuid == user_uuid)
                | (ORMGame.player2_uuid == user_uuid)
            )
            query = query.filter(ORMGame.status.in_([GameStatus.WON, GameStatus.DRAW]))
            orm_games = query.all()
            return [game_to_domain(orm) for orm in orm_games]
        finally:
            session.close()

    def get_leaderboard(self, limit: int) -> list[LeaderboardEntry]:
        if limit <= 0:
            raise ValueError("limit must be positive")

        session = self.session_factory()
        try:
            # Алиасы для таблицы games
            games_p1 = aliased(ORMGame)
            games_p2 = aliased(ORMGame)

            # Подзапрос: все участия в завершённых играх
            user_games = (
                select(
                    games_p1.player1_uuid.label("user_uuid"),
                    games_p1.status.label("status"),
                    games_p1.winner_uuid.label("winner_uuid"),
                )
                .where(games_p1.status.in_([GameStatus.WON, GameStatus.DRAW]))
                .union_all(
                    select(
                        games_p2.player2_uuid.label("user_uuid"),
                        games_p2.status.label("status"),
                        games_p2.winner_uuid.label("winner_uuid"),
                    ).where(games_p2.status.in_([GameStatus.WON, GameStatus.DRAW]))
                )
            ).subquery()

            # Агрегация по пользователю
            stats = (
                session.query(
                    user_games.c.user_uuid,
                    func.sum(
                        case(
                            (
                                and_(
                                    user_games.c.status == GameStatus.WON,
                                    user_games.c.winner_uuid == user_games.c.user_uuid,
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("wins"),
                    func.sum(
                        case(
                            (
                                and_(
                                    user_games.c.status == GameStatus.WON,
                                    # winner_uuid is NULL when the computer won; a plain
                                    # "!=" against NULL yields NULL, so that loss was not counted
                                    or_(
                                        user_games.c.winner_uuid.is_(None),
                                        user_games.c.winner_uuid != user_games.c.user_uuid,
                                    ),
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("losses"),
                    func.sum(
                        case((user_games.c.status == GameStatus.DRAW, 1), else_=0)
                    ).label("draws"),
                )
                .group_by(user_games.c.user_uuid)
                .having(func.count() > 0)
                .subquery()
            )

            # Float so the JSON value is always a number (NUMERIC came back as Decimal,
            # which Flask serialises as a string like "1.5000000000000000")
            win_ratio = cast(
                case(
                    (stats.c.losses + stats.c.draws == 0, stats.c.wins),
                    else_=stats.c.wins / (stats.c.losses + stats.c.draws),
                ),
                Float,
            ).label("win_ratio")

            # Основной запрос с JOIN users и вычислением win_ratio
            result = (
                session.query(
                    ORMUser.uuid,
                    ORMUser.login,
                    win_ratio,
                )
                .select_from(ORMUser)
                .join(stats, ORMUser.uuid == stats.c.user_uuid)
                .order_by(win_ratio.desc())
                .limit(limit)
                .all()
            )

            return [
                LeaderboardEntry(
                    user_uuid=row.uuid, login=row.login, win_ratio=row.win_ratio
                )
                for row in result
            ]
        finally:
            session.close()
