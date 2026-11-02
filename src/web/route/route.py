from flask import jsonify
from web.module.handlers import (
    create_game_handler,
    get_current_user_handler,
    get_game_history_handler,
    get_leaderboard_handler,
    list_games_handler,
    join_game_handler,
    get_game_handler,
    get_user_handler,
    refresh_access_handler,
    refresh_refresh_handler,
    signup_handler,
    login_handler,
    create_game_legacy_handler,
    update_game_handler,
)


def register_routes(app, service, auth_service, user_service):

    @app.route("/game", methods=["POST"])
    def create_game_legacy():
        data, status = create_game_legacy_handler(service)
        return jsonify(data), status

    @app.route("/game/<uuid_str>", methods=["POST"])
    def update_game(uuid_str):
        data, status = update_game_handler(uuid_str, service)
        return jsonify(data), status

    @app.route("/games", methods=["POST"])
    def create_game():
        data, status = create_game_handler(service)
        return jsonify(data), status

    @app.route("/games", methods=["GET"])
    def list_games():
        data, status = list_games_handler(service)
        return jsonify(data), status

    @app.route("/games/<uuid_str>/join", methods=["POST"])
    def join_game(uuid_str):
        data, status = join_game_handler(service, uuid_str)
        return jsonify(data), status

    @app.route("/games/<uuid_str>", methods=["GET"])
    def get_game(uuid_str):
        data, status = get_game_handler(service, uuid_str)
        return jsonify(data), status

    @app.route("/users/<uuid_str>", methods=["GET"])
    def get_user(uuid_str):
        data, status = get_user_handler(user_service, uuid_str)
        return jsonify(data), status

    @app.route("/signup", methods=["POST"])
    def signup():
        data, status = signup_handler(auth_service)
        return jsonify(data), status

    @app.route("/login", methods=["POST"])
    def login():
        data, status = login_handler(auth_service)
        return jsonify(data), status

    @app.route("/refresh/access", methods=["POST"])
    def refresh_access():
        data, status = refresh_access_handler(auth_service)
        return jsonify(data), status

    @app.route("/refresh/refresh", methods=["POST"])
    def refresh_refresh():
        data, status = refresh_refresh_handler(auth_service)
        return jsonify(data), status

    @app.route("/users/me", methods=["GET"])
    def get_current_user():
        data, status = get_current_user_handler(user_service)
        return jsonify(data), status

    @app.route("/games/history", methods=["GET"])
    def game_history():
        data, status = get_game_history_handler(service)
        return jsonify(data), status

    @app.route("/leaderboard", methods=["GET"])
    def get_leaderboard():
        data, status = get_leaderboard_handler(service)
        return jsonify(data), status
