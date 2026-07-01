from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domain.entities.session import Session as DomainSession
from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.session_id import SessionId
from domain.value_objects.user_id import UserId
from infrastructure.db.models import SessionRecord, UserRecord


def _to_domain_user(record: UserRecord) -> User:
    return User(
        id=UserId(record.id),
        email=Email(record.email),
        password_hash=PasswordHash(record.password_hash),
        role=record.role,
        created_at=record.created_at,
    )


def _to_domain_session(record: SessionRecord) -> DomainSession:
    return DomainSession(
        id=SessionId(record.id),
        user_id=UserId(record.user_id),
        token_hash=record.token_hash,
        expires_at=record.expires_at,
        created_at=record.created_at,
    )


class SqlAlchemyUserRepository:
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, user: User) -> User:
        record = self._db_session.get(UserRecord, user.id.value)
        if record is None:
            record = UserRecord(
                id=user.id.value,
                email=str(user.email),
                password_hash=str(user.password_hash),
                role=user.role,
                created_at=user.created_at,
            )
            self._db_session.add(record)
        else:
            record.email = str(user.email)
            record.password_hash = str(user.password_hash)
            record.role = user.role
            record.created_at = user.created_at

        self._db_session.flush()
        return _to_domain_user(record)

    def get_by_id(self, user_id: UserId) -> User | None:
        record = self._db_session.get(UserRecord, user_id.value)
        return _to_domain_user(record) if record else None

    def get_by_email(self, email: Email) -> User | None:
        stmt = select(UserRecord).where(UserRecord.email == str(email))
        record = self._db_session.scalar(stmt)
        return _to_domain_user(record) if record else None

    def list_all(self) -> list[User]:
        stmt = select(UserRecord).order_by(UserRecord.created_at.desc())
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_user(record) for record in records]

    def count_all(self) -> int:
        stmt = select(func.count()).select_from(UserRecord)
        return int(self._db_session.scalar(stmt) or 0)

    def list_page(self, *, offset: int, limit: int) -> list[User]:
        stmt = select(UserRecord).order_by(UserRecord.created_at.desc()).offset(offset).limit(limit)
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_user(record) for record in records]


class SqlAlchemySessionRepository:
    """SQLAlchemy implementation of SessionRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, session: DomainSession) -> DomainSession:
        record = self._db_session.get(SessionRecord, session.id.value)
        if record is None:
            record = SessionRecord(
                id=session.id.value,
                user_id=session.user_id.value,
                token_hash=session.token_hash,
                expires_at=session.expires_at,
                created_at=session.created_at,
            )
            self._db_session.add(record)
        else:
            record.user_id = session.user_id.value
            record.token_hash = session.token_hash
            record.expires_at = session.expires_at
            record.created_at = session.created_at

        self._db_session.flush()
        return _to_domain_session(record)

    def get_by_id(self, session_id: SessionId) -> DomainSession | None:
        record = self._db_session.get(SessionRecord, session_id.value)
        return _to_domain_session(record) if record else None

    def get_by_token_hash(self, token_hash: str) -> DomainSession | None:
        stmt = select(SessionRecord).where(SessionRecord.token_hash == token_hash)
        record = self._db_session.scalar(stmt)
        return _to_domain_session(record) if record else None

    def delete(self, session_id: SessionId) -> None:
        record = self._db_session.get(SessionRecord, session_id.value)
        if record is not None:
            self._db_session.delete(record)
            self._db_session.flush()
