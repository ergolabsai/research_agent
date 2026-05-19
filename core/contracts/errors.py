# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only


class DomainError(Exception):
    pass


class DuplicateEmail(DomainError):
    pass


class DuplicateUsername(DomainError):
    pass


class InvalidToken(DomainError):
    pass


class ExpiredToken(DomainError):
    pass
