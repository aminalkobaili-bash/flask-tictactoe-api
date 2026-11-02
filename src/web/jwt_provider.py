from uuid import UUID
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from domain.service.interface import JwtProvider
from domain.exceptions import JwtError


class JwtProviderImpl(JwtProvider):
    def generate_access_token(self, user_uuid: UUID) -> str:
        return create_access_token(identity=str(user_uuid))

    def generate_refresh_token(self, user_uuid: UUID) -> str:
        return create_refresh_token(identity=str(user_uuid))

    def _extract_uuid_from_token(self, token: str, expected_type: str) -> UUID:
        # flask-jwt-extended puts "type": "access" | "refresh" into every token.
        # Without this check a 7-day refresh token is accepted as an access token.
        try:
            data = decode_token(token)
        except Exception as e:
            raise JwtError(f"Invalid token: {str(e)}")
        if data.get("type") != expected_type:
            raise JwtError(f"Invalid token type: expected {expected_type} token")
        identity = data.get("sub")
        if identity is None:
            raise JwtError("Invalid token: missing identity")
        try:
            return UUID(identity)
        except ValueError:
            raise JwtError("Invalid token: malformed identity")

    def validate_access_token(self, token: str) -> UUID:
        return self._extract_uuid_from_token(token, "access")

    def validate_refresh_token(self, token: str) -> UUID:
        return self._extract_uuid_from_token(token, "refresh")
