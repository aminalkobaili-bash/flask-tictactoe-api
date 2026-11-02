from datasource.repository.interface import GameRepository, UserRepository
from domain.service.interface import GameService, JwtProvider, UserService, AuthService
from datasource.repository.postgres_repository import PostgresGameRepository
from datasource.repository.postgres_user_repository import PostgresUserRepository
from domain.service.impl import GameServiceImpl, UserServiceImpl, AuthServiceImpl
from database import SessionLocal
from web.jwt_provider import JwtProviderImpl


class Container:
    def __init__(self):
        self._game_repository = None
        self._game_service = None
        self._user_repository = None
        self._user_service = None
        self._auth_service = None
        self._jwt_provider = None

    def get_repository(self) -> GameRepository:
        if self._game_repository is None:
            self._game_repository = PostgresGameRepository(SessionLocal)
        return self._game_repository

    def get_service(self) -> GameService:
        if self._game_service is None:
            self._game_service = GameServiceImpl(self.get_repository())
        return self._game_service

    def get_user_repository(self) -> UserRepository:
        if self._user_repository is None:
            self._user_repository = PostgresUserRepository(SessionLocal)
        return self._user_repository

    def get_user_service(self) -> UserService:
        if self._user_service is None:
            self._user_service = UserServiceImpl(self.get_user_repository())
        return self._user_service

    def get_jwt_provider(self) -> JwtProvider:
        if self._jwt_provider is None:
            self._jwt_provider = JwtProviderImpl()
        return self._jwt_provider

    def get_auth_service(self) -> AuthService:
        if self._auth_service is None:
            self._auth_service = AuthServiceImpl(
                self.get_user_service(), self.get_jwt_provider()
            )
        return self._auth_service
