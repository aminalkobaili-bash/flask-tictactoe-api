class DomainError(Exception):
    """Базовое исключение для ошибок предметной области."""

    pass


class InvalidMoveError(DomainError):
    pass


class GameOverError(DomainError):
    pass


class GameNotFoundError(DomainError):
    pass


class GameNotWaitingError(DomainError):
    pass


class WrongPlayerTurnError(DomainError):
    pass


class JwtError(DomainError):
    """Ошибка при работе с JWT (недействительный, просроченный токен и т.д.)."""

    pass
