from typing import List


class UpdateGameRequest:
    def __init__(self, field: List[List[int]]):
        self.field = field

    @classmethod
    def from_json(cls, data: dict) -> "UpdateGameRequest":
        field = data.get("field")
        if field is None:
            raise ValueError("Missing 'field' in request body")
        if not isinstance(field, list) or len(field) != 3:
            raise ValueError("Field must be a 3x3 matrix")
        for row in field:
            if not isinstance(row, list) or len(row) != 3:
                raise ValueError("Field must be a 3x3 matrix")
            for cell in row:
                if cell not in (0, 1, 2):
                    raise ValueError("Cell values must be 0, 1, or 2")
        return cls(field)


class SignUpRequest:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password

    @classmethod
    def from_json(cls, data: dict):
        login = data.get("login")
        password = data.get("password")
        if not login or not password:
            raise ValueError("Login and password are required")
        return cls(login, password)


class JwtRequest:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password

    @classmethod
    def from_json(cls, data: dict) -> "JwtRequest":
        login = data.get("login")
        password = data.get("password")
        if not login or not password:
            raise ValueError("Login and password are required")
        return cls(login, password)


class RefreshJwtRequest:
    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token

    @classmethod
    def from_json(cls, data: dict) -> "RefreshJwtRequest":
        refresh_token = data.get("refreshToken")
        if not refresh_token:
            raise ValueError("refreshToken is required")
        return cls(refresh_token)
