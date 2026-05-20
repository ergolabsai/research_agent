# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pyseto
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from pyseto import Key

from core.contracts.auth import UserId
from core.contracts.errors import ExpiredToken, InvalidToken
from core.contracts.tokens import RefreshToken, TokenClaims


class PasetoTokenIssuer:
    """TokenIssuer adapter backed by PASETO v4.public (Ed25519).

    v4.public uses Ed25519 signing — no algorithm is negotiated at runtime,
    eliminating the algorithm-confusion class of vulnerabilities present in JWT.

    Key generation (run once, store in .env):
        openssl genpkey -algorithm ed25519 -out ed25519_private.pem
        openssl pkey -in ed25519_private.pem -pubout -out ed25519_public.pem
    """

    _REFRESH_TTL = timedelta(days=7)

    def __init__(self, private_key_pem: str, public_key_pem: str) -> None:
        _priv = load_pem_private_key(private_key_pem.encode(), password=None)
        _pub = load_pem_public_key(public_key_pem.encode())
        self._private_key = Key.new(version=4, purpose="public", key=_priv)
        self._public_key = Key.new(version=4, purpose="public", key=_pub)

    # --- helpers ---

    def _decode(self, token: str) -> dict:
        try:
            decoded = pyseto.decode(self._public_key, token, deserializer=json)
        except pyseto.ValidationError as e:
            # ValidationError covers exp, nbf, iat, and malformed claim values.
            # Only map to ExpiredToken when the failure is clearly expiry-related;
            # treat all other validation failures as InvalidToken.
            msg = str(e).lower()
            if "exp" in msg or "expired" in msg:
                raise ExpiredToken(token)
            raise InvalidToken(token)
        except pyseto.PasetoError:
            raise InvalidToken(token)
        return decoded.payload

    # --- TokenIssuer protocol ---

    async def mint_access_token(self, claims: TokenClaims) -> str:
        payload = {
            "sub": claims.sub,
            "email": claims.email,
            "roles": claims.roles,
            "is_guest": claims.is_guest,
            # iat stored in payload so it round-trips unchanged
            "iat": claims.iat.astimezone(timezone.utc).isoformat(),
        }
        token = pyseto.encode(
            self._private_key,
            payload,
            serializer=json,
            exp=claims.exp.astimezone(timezone.utc),
        )
        return token.decode()

    async def verify_access_token(self, token: str) -> TokenClaims:
        payload = self._decode(token)
        try:
            return TokenClaims(
                sub=payload["sub"],
                email=payload["email"],
                roles=payload.get("roles", []),
                is_guest=payload.get("is_guest", False),
                iat=datetime.fromisoformat(payload["iat"]),
                exp=datetime.fromisoformat(payload["exp"]),
            )
        except (KeyError, ValueError, TypeError):
            raise InvalidToken(token)

    async def mint_refresh_token(self, user_id: UserId) -> RefreshToken:
        token_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + self._REFRESH_TTL
        payload = {
            "sub": str(user_id),
            "jti": token_id,
            "type": "refresh",
        }
        token = pyseto.encode(
            self._private_key,
            payload,
            serializer=json,
            exp=expires_at,
        )
        return RefreshToken(
            token=token.decode(),
            token_id=token_id,
            user_id=user_id,
            expires_at=expires_at,
        )

    async def verify_refresh_token(self, token: str) -> RefreshToken | None:
        # Protocol contract: return None for invalid/unrecognised tokens;
        # raise ExpiredToken for tokens that were valid but have since expired.
        try:
            payload = self._decode(token)
        except InvalidToken:
            return None
        # ExpiredToken propagates naturally from _decode.
        if payload.get("type") != "refresh":
            return None
        try:
            return RefreshToken(
                token=token,
                token_id=payload["jti"],
                user_id=UserId(int(payload["sub"])),
                expires_at=datetime.fromisoformat(payload["exp"]),
            )
        except (KeyError, ValueError, TypeError):
            return None

    async def revoke_refresh_token(self, token_id: str) -> None:
        # Stateless — no denylist yet. Tokens expire naturally.
        # A persistent denylist (SQLite table) is tracked in the architecture backlog.
        pass
