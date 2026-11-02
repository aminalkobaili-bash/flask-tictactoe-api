from datasource.orm.user import User as ORMUser
from domain.model.user import User


def user_to_domain(orm_user: ORMUser) -> User:
    return User(
        uuid=orm_user.uuid,
        login=orm_user.login,
        password=orm_user.password,
    )


def user_to_orm(user: User) -> ORMUser:
    return ORMUser(
        uuid=user.uuid,
        login=user.login,
        password=user.password,
    )
