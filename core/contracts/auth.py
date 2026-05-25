# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from enum import StrEnum
from typing import NewType

from pydantic import BaseModel

UserId = NewType("UserId", int)


class Role(StrEnum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class PrincipalSource(StrEnum):
    JWT = "jwt"
    SYSTEM = "system"
    CLI = "cli"


class Principal(BaseModel):
    """Authenticated caller identity. Passed as the first argument to every use case."""

    user_id: UserId
    email: str
    roles: list[Role]
    is_guest: bool = False
    source: PrincipalSource = PrincipalSource.JWT

    model_config = {"frozen": True}

    def has_role(self, role: Role) -> bool:
        return role in self.roles
