# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.contracts.auth import Role, UserId
from core.contracts.errors import InvalidCredentials
from core.contracts.tokens import RefreshToken, TokenClaims
from core.contracts.users import User
from core.ports.password_hasher import PasswordHasher
from core.ports.repositories import UserRepository
from core.ports.token_issuer import TokenIssuer


@dataclass(frozen=True)
class LoginUserRequest:
    identifier: str  # email or username
    password: str


@dataclass(frozen=True)
class LoginUserResponse:
    access_token: str
    refresh_token: RefreshToken
    user: User


class LoginUser:
    """
    Authenticate an existing user by identifier (email or username) and password.

    Raises InvalidCredentials for both unknown identifiers and wrong passwords —
    a single error type prevents callers from distinguishing the two cases,
    which would allow username enumeration.

    If the stored hash was produced with outdated bcrypt parameters, the hash is
    transparently re-computed and persisted on successful login (needs_rehash path).
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

    async def execute(self, request: LoginUserRequest) -> LoginUserResponse:
        user = await self._user_repo.get_by_identifier(request.identifier)
        if user is None:
            raise InvalidCredentials()

        verified = await self._hasher.verify(request.password, user.hashed_password)
        if not verified:
            raise InvalidCredentials()

        # Transparently re-hash if bcrypt work factor has changed since the
        # password was last stored.
        if await self._hasher.needs_rehash(user.hashed_password):
            new_hash = await self._hasher.hash(request.password)
            user = await self._user_repo.update(
                user.model_copy(update={"hashed_password": new_hash})
            )

        now = datetime.now(timezone.utc)
        claims = TokenClaims(
            sub=str(user.id),
            email=user.email,
            roles=[Role.GUEST if user.is_guest else Role.USER],
            is_guest=user.is_guest,
            iat=now,
            exp=now + self._access_token_ttl,
        )
        access_token = await self._tokens.mint_access_token(claims)
        refresh_token = await self._tokens.mint_refresh_token(UserId(user.id))

        return LoginUserResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user,
        )
