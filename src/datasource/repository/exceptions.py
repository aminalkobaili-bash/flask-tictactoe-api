class RepositoryError(Exception):
    """Базовое исключение для репозиториев."""

    pass


class DuplicateRepositoryError(RepositoryError):
    """Возникает при попытке создать запись с дублирующим уникальным полем."""

    pass
