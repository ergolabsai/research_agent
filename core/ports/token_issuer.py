# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Protocol, runtime_checkable

from core.contracts.auth import UserId
from core.contracts.tokens import RefreshToken, TokenClaims


@runtime_checkable
class TokenIssuer(Protocol):
    async def mint_access_token(self, claims: TokenClaims) -> str: ...
    async def mint_refresh_token(self, user_id: UserId) -> RefreshToken: ...
    async def verify_access_token(self, token: str) -> TokenClaims: ...
    # Returns None if the token is not found (already revoked or never issued).
    # Raises ExpiredToken if the token is found but past its expiry.
    async def verify_refresh_token(self, token: str) -> RefreshToken | None: ...
    async def revoke_refresh_token(self, token_id: str) -> None: ...
