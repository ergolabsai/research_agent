# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from core.contracts.auth import UserId


class User(BaseModel):
    """Core user entity. Pure Pydantic — no SQLModel or DB concerns."""

    id: Optional[UserId] = None
    email: str
    username: str
    hashed_password: str
    is_guest: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"frozen": True}
