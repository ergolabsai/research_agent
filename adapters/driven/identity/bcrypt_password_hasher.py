# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

import bcrypt


class BcryptPasswordHasher:
    """PasswordHasher adapter backed by bcrypt."""

    def __init__(self, work_factor: int = 12) -> None:
        self._work_factor = work_factor

    async def hash(self, password: str) -> str:
        salt = bcrypt.gensalt(rounds=self._work_factor)
        return bcrypt.hashpw(password.encode(), salt).decode()

    async def verify(self, password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except (ValueError, TypeError):
            return False

    async def needs_rehash(self, hashed: str) -> bool:
        # bcrypt encodes the work factor in the hash string: $2b$RR$...
        parts = hashed.split("$")
        try:
            return int(parts[2]) != self._work_factor
        except (IndexError, ValueError):
            return True