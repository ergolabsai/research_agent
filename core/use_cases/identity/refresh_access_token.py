# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.contracts.auth import Role
from core.contracts.errors import InvalidToken
from core.contracts.tokens import RefreshToken, TokenClaims
from core.contracts.users import User
from core.ports.repositories import UserRepository
from core.ports.token_issuer import TokenIssuer


@dataclass(frozen=True)
class RefreshAccessTokenRequest:
    refresh_token: str


@dataclass(frozen=True)
class RefreshAccessTokenResponse:
    access_token: str
    refresh_token: RefreshToken
    user: User


class RefreshAccessToken:
    """
    Exchange a valid refresh token for a new access token and a rotated refresh token.

    The presented refresh token is revoked and replaced on every successful call
    (rotation). If a stolen token is replayed after the legitimate user has already
    refreshed, the second use will fail — surfacing the compromise.

    Access token claims are rebuilt from the current user record so role or guest-status
    changes since the original login take effect on the next refresh.
    """

    _DEFAULT_ACCESS_TTL = timedelta(minutes=15)

    def __init__(
        self,
        user_repo: UserRepository,
        token_issuer: TokenIssuer,
        access_token_ttl: timedelta = _DEFAULT_ACCESS_TTL,
    ) -> None:
        self._user_repo = user_repo
        self._tokens = token_issuer
        self._access_token_ttl = access_token_ttl

    async def execute(
        self, request: RefreshAccessTokenRequest
    ) -> RefreshAccessTokenResponse:
        stored = await self._tokens.verify_refresh_token(request.refresh_token)
        if stored is None:
            raise InvalidToken()

        user = await self._user_repo.get(stored.user_id)
        if user is None:
            # Account was deleted after the refresh token was issued.
            await self._tokens.revoke_refresh_token(stored.token_id)
            raise InvalidToken()

        await self._tokens.revoke_refresh_token(stored.token_id)
        new_refresh = await self._tokens.mint_refresh_token(stored.user_id)

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

        return RefreshAccessTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            user=user,
        )
