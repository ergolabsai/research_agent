# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

from sqlmodel import Session, select

from app.models import User as SqlUser
from app.time import now
from core.contracts.auth import UserId
from core.contracts.users import User


class SqliteUserRepository:
    """UserRepository adapter backed by SQLite via SQLModel.

    Expects a request-scoped Session injected by the composition layer.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # --- mapping helpers ---

    def _to_contract(self, row: SqlUser) -> User:
        return User(
            id=UserId(row.id),
            email=row.email,
            username=row.username,
            hashed_password=row.hashed_password,
            is_guest=row.email.startswith("guest+") or row.username.startswith("guest_"),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # --- UserRepository protocol ---

    async def create(self, user: User) -> User:
        row = SqlUser(
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return self._to_contract(row)

    async def get(self, user_id: UserId) -> User | None:
        row = self._session.get(SqlUser, user_id)
        return self._to_contract(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        row = self._session.exec(select(SqlUser).where(SqlUser.email == email)).first()
        return self._to_contract(row) if row else None

    async def get_by_username(self, username: str) -> User | None:
        row = self._session.exec(select(SqlUser).where(SqlUser.username == username)).first()
        return self._to_contract(row) if row else None

    async def update(self, user: User) -> User:
        row = self._session.get(SqlUser, user.id)
        if row is None:
            raise ValueError(f"User {user.id} not found")
        row.email = user.email
        row.username = user.username
        row.hashed_password = user.hashed_password
        row.updated_at = now()
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return self._to_contract(row)

    async def delete(self, user_id: UserId) -> None:
        row = self._session.get(SqlUser, user_id)
        if row is not None:
            self._session.delete(row)
            self._session.commit()

    async def search(self, query: str, *, limit: int = 50) -> list[User]:
        rows = self._session.exec(
            select(SqlUser)
            .where((SqlUser.email.contains(query)) | (SqlUser.username.contains(query)))
            .limit(limit)
        ).all()
        return [self._to_contract(row) for row in rows]