# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime

from pydantic import BaseModel

from core.contracts.auth import UserId


class TokenClaims(BaseModel):
    """Decoded claims from a verified access token."""

    sub: str
    email: str
    roles: list[str]
    is_guest: bool = False
    iat: datetime
    exp: datetime

    model_config = {"frozen": True}


class RefreshToken(BaseModel):
    """Stateful refresh token. The adapter persists and rotates these."""

    token: str
    token_id: str
    user_id: UserId
    expires_at: datetime

    model_config = {"frozen": True}
