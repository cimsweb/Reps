"""In-memory repository fakes for unit tests."""

from domain.entities.session import Session
from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.session_id import SessionId
from domain.value_objects.user_id import UserId


class InMemoryUserRepository:
    """Simple in-memory UserRepository for tests."""

    def __init__(self) -> None:
        self._users_by_id: dict[UserId, User] = {}
        self._users_by_email: dict[str, User] = {}

    def save(self, user: User) -> User:
        self._users_by_id[user.id] = user
        self._users_by_email[str(user.email)] = user
        return user

    def get_by_id(self, user_id: UserId) -> User | None:
        return self._users_by_id.get(user_id)

    def get_by_email(self, email: Email) -> User | None:
        return self._users_by_email.get(str(email))

    def list_all(self) -> list[User]:
        return sorted(self._users_by_id.values(), key=lambda user: user.created_at, reverse=True)

    def count_all(self) -> int:
        return len(self._users_by_id)

    def list_page(self, *, offset: int, limit: int) -> list[User]:
        return self.list_all()[offset : offset + limit]


class InMemorySessionRepository:
    """Simple in-memory SessionRepository for tests."""

    def __init__(self) -> None:
        self._sessions_by_id: dict[SessionId, Session] = {}
        self._sessions_by_token_hash: dict[str, Session] = {}

    def save(self, session: Session) -> Session:
        self._sessions_by_id[session.id] = session
        self._sessions_by_token_hash[session.token_hash] = session
        return session

    def get_by_id(self, session_id: SessionId) -> Session | None:
        return self._sessions_by_id.get(session_id)

    def get_by_token_hash(self, token_hash: str) -> Session | None:
        return self._sessions_by_token_hash.get(token_hash)

    def delete(self, session_id: SessionId) -> None:
        session = self._sessions_by_id.pop(session_id, None)
        if session is not None:
            self._sessions_by_token_hash.pop(session.token_hash, None)
