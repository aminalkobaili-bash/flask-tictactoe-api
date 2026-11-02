from uuid import UUID
from flask import request, g

from domain.exceptions import (
    DomainError,
    InvalidMoveError,
    GameOverError,
    GameNotFoundError,
    GameNotWaitingError,
    WrongPlayerTurnError,
)
from domain.model.game_type import GameType
from domain.service.interface import GameService, UserService, AuthService
from web.model.leaderboard_response import LeaderboardResponse
from web.model.request import (
    JwtRequest,
    RefreshJwtRequest,
    SignUpRequest,
    UpdateGameRequest,
)
from web.model.response import JwtResponse, UserResponse
from web.model.error_response import ErrorResponse
from web.mapper.mapper import matrix_to_domain_field, game_to_response


def _create_game_and_response(
    service: GameService, game_type: GameType
) -> tuple[dict, int]:
    """Создаёт игру указанного типа и возвращает JSON-ответ с кодом."""
    user_uuid = g.get("user_uuid")  # always present due to before_request
    try:
        game = service.create_game(user_uuid, game_type)
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 400
    return game_to_response(game).to_json(), 201


def create_game_handler(service: GameService):
    json_data = request.get_json()
    if not json_data:
        return ErrorResponse("Invalid JSON").to_json(), 400

    game_type_str = json_data.get("game_type", "computer")
    try:
        game_type = GameType(game_type_str)
    except ValueError:
        return ErrorResponse(
            "Invalid game_type. Must be 'computer' or 'human'"
        ).to_json(), 400

    return _create_game_and_response(service, game_type)


def list_games_handler(service: GameService):
    user_uuid = g.get("user_uuid")
    try:
        games = service.list_waiting_games(user_uuid)
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 400

    return {"games": [game_to_response(g).to_json() for g in games]}, 200


def join_game_handler(service: GameService, uuid_str: str):
    try:
        game_uuid = UUID(uuid_str)
    except ValueError:
        return ErrorResponse("Invalid UUID format").to_json(), 400

    user_uuid = g.get("user_uuid")

    try:
        game = service.join_game(game_uuid, user_uuid)
    except GameNotWaitingError as e:
        return ErrorResponse("Game is not waiting", details=str(e)).to_json(), 400
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 400

    return game_to_response(game).to_json(), 200


def get_game_handler(service: GameService, uuid_str: str):
    try:
        game_uuid = UUID(uuid_str)
    except ValueError:
        return ErrorResponse("Invalid UUID format").to_json(), 400

    try:
        game = service.get_game(game_uuid)
    except GameNotFoundError:
        return ErrorResponse("Game not found").to_json(), 404
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 400

    return game_to_response(game).to_json(), 200


def get_user_handler(service: UserService, uuid_str: str):
    try:
        user_uuid = UUID(uuid_str)
    except ValueError:
        return ErrorResponse("Invalid UUID format").to_json(), 400

    try:
        user = service.get_by_uuid(user_uuid)
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 400

    if not user:
        return ErrorResponse("User not found").to_json(), 404

    response = UserResponse(uuid=user.uuid, login=user.login)
    return response.to_json(), 200


def create_game_legacy_handler(service: GameService):
    return _create_game_and_response(service, GameType.COMPUTER)


def update_game_handler(uuid_str: str, service: GameService):
    try:
        game_uuid = UUID(uuid_str)
    except ValueError:
        return ErrorResponse("Invalid UUID format").to_json(), 400

    json_data = request.get_json()
    if json_data is None:
        return ErrorResponse("Invalid JSON body").to_json(), 400

    try:
        req = UpdateGameRequest.from_json(json_data)
    except ValueError as e:
        return ErrorResponse("Invalid request data", details=str(e)).to_json(), 400

    try:
        updated_field = matrix_to_domain_field(req.field)
    except ValueError as e:
        return ErrorResponse("Invalid field data", details=str(e)).to_json(), 400

    user_uuid = g.get("user_uuid")

    try:
        updated_game = service.make_move(game_uuid, user_uuid, updated_field)
    except (InvalidMoveError, GameOverError, WrongPlayerTurnError) as e:
        return ErrorResponse("Move failed", details=str(e)).to_json(), 400
    except DomainError as e:
        return ErrorResponse("Error", details=str(e)).to_json(), 400

    return game_to_response(updated_game).to_json(), 200


def signup_handler(auth_service: AuthService):
    json_data = request.get_json()
    if not json_data:
        return ErrorResponse("Invalid JSON").to_json(), 400
    try:
        req = SignUpRequest.from_json(json_data)
    except ValueError as e:
        return ErrorResponse(str(e)).to_json(), 400
    try:
        auth_service.register(req.login, req.password)
        return {"message": "User registered successfully"}, 201
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 400


def login_handler(auth_service: AuthService):
    json_data = request.get_json()
    if not json_data:
        return ErrorResponse("Invalid JSON").to_json(), 400
    try:
        req = JwtRequest.from_json(json_data)
    except ValueError as e:
        return ErrorResponse(str(e)).to_json(), 400

    try:
        tokens = auth_service.authenticate(req.login, req.password)
        response = JwtResponse(tokens.access_token, tokens.refresh_token)
        return response.to_json(), 200
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 401


def refresh_access_handler(auth_service: AuthService):
    json_data = request.get_json()
    if not json_data:
        return ErrorResponse("Invalid JSON").to_json(), 400
    try:
        req = RefreshJwtRequest.from_json(json_data)
    except ValueError as e:
        return ErrorResponse(str(e)).to_json(), 400

    try:
        tokens = auth_service.refresh_access_token(req.refresh_token)
        response = JwtResponse(tokens.access_token, tokens.refresh_token)
        return response.to_json(), 200
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 401


def refresh_refresh_handler(auth_service: AuthService):
    json_data = request.get_json()
    if not json_data:
        return ErrorResponse("Invalid JSON").to_json(), 400
    try:
        req = RefreshJwtRequest.from_json(json_data)
    except ValueError as e:
        return ErrorResponse(str(e)).to_json(), 400

    try:
        tokens = auth_service.refresh_refresh_token(req.refresh_token)
        response = JwtResponse(tokens.access_token, tokens.refresh_token)
        return response.to_json(), 200
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 401


def get_current_user_handler(user_service: UserService):
    user_uuid = g.get("user_uuid")
    if user_uuid is None:
        return ErrorResponse("Unauthorized").to_json(), 401
    user = user_service.get_by_uuid(user_uuid)
    if user is None:
        return ErrorResponse("User not found").to_json(), 404
    response = UserResponse(uuid=user.uuid, login=user.login)
    return response.to_json(), 200


def get_game_history_handler(service: GameService):
    user_uuid = g.get("user_uuid")
    if user_uuid is None:
        return ErrorResponse("Unauthorized").to_json(), 401
    try:
        games = service.list_finished_games(user_uuid)
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 400
    return {"games": [game_to_response(g).to_json() for g in games]}, 200


def get_leaderboard_handler(service: GameService):
    # Извлекаем параметр limit из query-строки
    limit_str = request.args.get("limit")
    if limit_str is None:
        return ErrorResponse("Missing required parameter: limit").to_json(), 400
    try:
        limit = int(limit_str)
        if limit <= 0:
            raise ValueError
    except ValueError:
        return ErrorResponse("limit must be a positive integer").to_json(), 400

    try:
        entries = service.get_leaderboard(limit)
    except DomainError as e:
        return ErrorResponse(str(e)).to_json(), 400

    response = [
        LeaderboardResponse(
            user_uuid=entry.user_uuid, login=entry.login, win_ratio=entry.win_ratio
        )
        for entry in entries
    ]
    return {"leaderboard": [r.to_json() for r in response]}, 200
