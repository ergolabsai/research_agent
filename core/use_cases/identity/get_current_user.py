# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass

from core.contracts.auth import Principal
from core.contracts.errors import InvalidToken
from core.contracts.users import User
from core.ports.repositories import UserRepository


@dataclass(frozen=True)
class GetCurrentUserResponse:
    user: User


class GetCurrentUser:
    """
    Resolve the authenticated caller's full user record.

    The principal is already authenticated upstream (its token has been verified),
    so this use case only re-reads the user row. If the row is missing — the
    account was deleted after the token was issued — InvalidToken is raised so
    the caller treats the token as no longer usable.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, principal: Principal) -> GetCurrentUserResponse:
        user = await self._user_repo.get(principal.user_id)
        if user is None:
            raise InvalidToken()
        return GetCurrentUserResponse(user=user)
