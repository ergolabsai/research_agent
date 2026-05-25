# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

import uuid
from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt

from core.contracts.auth import UserId
from core.contracts.errors import ExpiredToken, InvalidToken
from core.contracts.tokens import RefreshToken, TokenClaims


class JoseTokenIssuer:
    """TokenIssuer adapter backed by python-jose (HS256)."""

    _ALGORITHM = "HS256"
    _REFRESH_TTL = timedelta(days=7)

    def __init__(self, secret_key: str) -> None:
        self._secret_key = secret_key

    async def mint_access_token(self, claims: TokenClaims) -> str:
        payload = {
            "sub": claims.sub,
            "email": claims.email,
            "roles": claims.roles,
            "is_guest": claims.is_guest,
            "iat": claims.iat.astimezone(timezone.utc),
            "exp": claims.exp.astimezone(timezone.utc),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._ALGORITHM)

    async def mint_refresh_token(self, user_id: UserId) -> RefreshToken:
        token_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + self._REFRESH_TTL
        payload = {
            "sub": str(user_id),
            "jti": token_id,
            "type": "refresh",
            "iat": now,
            "exp": expires_at,
        }
        token = jwt.encode(payload, self._secret_key, algorithm=self._ALGORITHM)
        return RefreshToken(token=token, token_id=token_id, user_id=user_id, expires_at=expires_at)

    async def verify_access_token(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._ALGORITHM])
        except ExpiredSignatureError:
            raise ExpiredToken(token)
        except JWTError:
            raise InvalidToken(token)

        return TokenClaims(
            sub=payload["sub"],
            email=payload["email"],
            roles=payload.get("roles", []),
            is_guest=payload.get("is_guest", False),
            # Note: python-jose returns iat/exp as unix timestamps, not datetimes
            # Encode iat/exp as numeric timestamps in mint_access_token to ensure consistent timezone handling across implementations
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),    
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),    
        )

    async def verify_refresh_token(self, token: str) -> RefreshToken | None:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._ALGORITHM])
        except ExpiredSignatureError:
            raise ExpiredToken(token)
        except JWTError:
            return None

        if payload.get("type") != "refresh":
            return None

        return RefreshToken(
            token=token,
            token_id=payload["jti"],
            user_id=UserId(int(payload["sub"])),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )

    async def revoke_refresh_token(self, token_id: str) -> None:
        # Refresh tokens are currently stateless JWTs — no denylist exists yet.
        # Tokens expire naturally. A persistent denylist is tracked in the architecture backlog.
        pass