from datasource.orm.game import Game as ORMGame
from domain.model.game import Game
from domain.model.field import GameField


def game_to_domain(orm_game: ORMGame) -> Game:
    return Game(
        uuid=orm_game.uuid,
        field=GameField(matrix=orm_game.field_matrix),
        created_at=orm_game.created_at,
        player1_uuid=orm_game.player1_uuid,
        player2_uuid=orm_game.player2_uuid,
        status=orm_game.status,
        current_turn_uuid=orm_game.current_turn_uuid,
        winner_uuid=orm_game.winner_uuid,
        player1_symbol=orm_game.player1_symbol,
        player2_symbol=orm_game.player2_symbol,
        game_type=orm_game.game_type,
    )


def game_to_orm(game: Game) -> ORMGame:
    return ORMGame(
        uuid=game.uuid,
        field_matrix=game.field.matrix,
        created_at=game.created_at,
        player1_uuid=game.player1_uuid,
        player2_uuid=game.player2_uuid,
        status=game.status,
        current_turn_uuid=game.current_turn_uuid,
        winner_uuid=game.winner_uuid,
        player1_symbol=game.player1_symbol,
        player2_symbol=game.player2_symbol,
        game_type=game.game_type,
    )
