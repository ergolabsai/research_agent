# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Protocol, runtime_checkable


@runtime_checkable
class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str: ...
    async def verify(self, password: str, hashed: str) -> bool: ...
    # Returns True when the stored hash was produced with outdated parameters.
    # The login use case re-hashes on next successful login when this is True.
    async def needs_rehash(self, hashed: str) -> bool: ...
