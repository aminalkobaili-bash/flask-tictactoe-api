import os

from flask import Flask, g, request
from di.container import Container
from domain.exceptions import JwtError
from web.route.route import register_routes
from database import engine, Base
from flask_jwt_extended import JWTManager
import config


def create_app():
    app = Flask(__name__)

    app.config.from_object(config)

    jwt = JWTManager(app)

    Base.metadata.create_all(engine)

    container = Container()
    jwt_provider = container.get_jwt_provider()

    @app.before_request
    def authenticate():
        # Пропускаем маршруты, которые не требуют авторизации
        if request.endpoint in ["signup", "login", "refresh_access", "refresh_refresh"]:
            return

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {
                "error": "Unauthorized",
                "message": "Bearer token required",
            }, 401

        token = auth_header.split(" ")[1]
        try:
            user_uuid = jwt_provider.validate_access_token(token)
            g.user_uuid = user_uuid
        except JwtError as e:
            return {
                "error": "Unauthorized",
                "message": str(e),
            }, 401

    register_routes(
        app,
        container.get_service(),
        container.get_auth_service(),
        container.get_user_service(),
    )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
