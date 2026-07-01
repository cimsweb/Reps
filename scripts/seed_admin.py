#!/usr/bin/env python3
"""Create or update the admin user from .env."""

from sqlalchemy.orm import Session

from infrastructure.config.env import load_environment
from infrastructure.db.engine import create_db_engine
from infrastructure.db.repositories import SqlAlchemyUserRepository
from infrastructure.db.seed_admin import seed_admin_user, upsert_admin_user
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher


def main() -> None:
    load_environment()
    engine = create_db_engine()
    with Session(engine) as db_session:
        repository = SqlAlchemyUserRepository(db_session)
        hasher = ScryptPasswordHasher()
        user = seed_admin_user(repository, hasher)
        if user is None:
            user = upsert_admin_user(repository, hasher)
        db_session.commit()

    if user is None:
        print("Admin user already exists and password is unchanged")
        return

    print(f"Admin user ready: {user.email}")


if __name__ == "__main__":
    main()
