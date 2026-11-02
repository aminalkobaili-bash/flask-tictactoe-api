from domain.model.field import GameField
from domain.model.game import Game
from web.model.response import GameResponse


def domain_field_to_web_matrix(field: GameField) -> list[list[int]]:
    return [list(row) for row in field.matrix]


def matrix_to_domain_field(matrix: list[list[int]]) -> GameField:
    return GameField(matrix=[list(row) for row in matrix])


def game_to_response(game: Game) -> GameResponse:
    """Преобразует доменную игру в веб-ответ."""
    return GameResponse(
        uuid=game.uuid,
        field=domain_field_to_web_matrix(game.field),
        status=game.status,
        player1_uuid=game.player1_uuid,
        player2_uuid=game.player2_uuid,
        current_turn_uuid=game.current_turn_uuid,
        winner_uuid=game.winner_uuid,
        game_type=game.game_type,
    )
