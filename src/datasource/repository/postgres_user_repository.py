from typing import Optional
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from datasource.orm.user import User as ORMUser
from domain.model.user import User
from datasource.repository.interface import UserRepository
from datasource.repository.exceptions import DuplicateRepositoryError
from datasource.mapper import user_to_domain, user_to_orm


class PostgresUserRepository(UserRepository):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save(self, user: User) -> None:
        session = self.session_factory()
        try:
            orm_user = user_to_orm(user)
            session.add(orm_user)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise DuplicateRepositoryError()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_login(self, login: str) -> Optional[User]:
        session = self.session_factory()
        try:
            orm_user = session.query(ORMUser).filter(ORMUser.login == login).first()
            if orm_user is None:
                return None
            return user_to_domain(orm_user)
        finally:
            session.close()

    def get_by_uuid(self, uuid: UUID) -> Optional[User]:
        session = self.session_factory()
        try:
            orm_user = session.query(ORMUser).filter(ORMUser.uuid == uuid).first()
            if orm_user is None:
                return None
            return user_to_domain(orm_user)
        finally:
            session.close()
