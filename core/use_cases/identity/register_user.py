# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.contracts.auth import Principal, Role, UserId
from core.contracts.errors import DuplicateEmail, DuplicateUsername
from core.contracts.tokens import RefreshToken, TokenClaims
from core.contracts.users import User
from core.ports.password_hasher import PasswordHasher
from core.ports.repositories import UserRepository
from core.ports.token_issuer import TokenIssuer


@dataclass(frozen=True)
class RegisterUserRequest:
    email: str
    username: str
    password: str


@dataclass(frozen=True)
class RegisterUserResponse:
    access_token: str
    refresh_token: RefreshToken
    user: User


class RegisterUser:
    """
    Create a new user account and return tokens.

    If the caller is an authenticated guest (principal.is_guest is True),
    the existing guest account is converted in-place rather than creating a new row.
    """

    _DEFAULT_ACCESS_TTL = timedelta(minutes=15)

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        token_issuer: TokenIssuer,
        access_token_ttl: timedelta = _DEFAULT_ACCESS_TTL,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = password_hasher
        self._tokens = token_issuer
        self._access_token_ttl = access_token_ttl

    async def execute(
        self,
        principal: Optional[Principal],
        request: RegisterUserRequest,
    ) -> RegisterUserResponse:
        guest_id: Optional[UserId] = (
            principal.user_id if (principal and principal.is_guest) else None
        )

        existing_email = await self._user_repo.get_by_email(request.email)
        if existing_email and existing_email.id != guest_id:
            raise DuplicateEmail(request.email)

        # Prevent a new email from shadowing an existing username in identifier lookup.
        email_as_username = await self._user_repo.get_by_username(request.email)
        if email_as_username and email_as_username.id != guest_id:
            raise DuplicateEmail(request.email)

        existing_username = await self._user_repo.get_by_username(request.username)
        if existing_username and existing_username.id != guest_id:
            raise DuplicateUsername(request.username)

        # Prevent a new username from shadowing an existing email in identifier lookup.
        username_as_email = await self._user_repo.get_by_email(request.username)
        if username_as_email and username_as_email.id != guest_id:
            raise DuplicateUsername(request.username)

        hashed = await self._hasher.hash(request.password)

        if guest_id is not None:
            guest = await self._user_repo.get(guest_id)
            user = await self._user_repo.update(
                guest.model_copy(
                    update={
                        "email": request.email,
                        "username": request.username,
                        "hashed_password": hashed,
                        "is_guest": False,
                    }
                )
            )
        else:
            user = await self._user_repo.create(
                User(
                    email=request.email,
                    username=request.username,
                    hashed_password=hashed,
                    is_guest=False,
                )
            )

        now = datetime.now(timezone.utc)
        claims = TokenClaims(
            sub=str(user.id),
            email=user.email,
            roles=[Role.USER],
            is_guest=False,
            iat=now,
            exp=now + self._access_token_ttl,
        )
        access_token = await self._tokens.mint_access_token(claims)
        refresh_token = await self._tokens.mint_refresh_token(user.id)

        return RegisterUserResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user,
        )
