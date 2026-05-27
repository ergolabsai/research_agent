# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Authorization primitives.

See architecture decision 0005 (Principal in every use-case) and
capabilities/identity/0003 (role-based, not policy engine).
"""

from enum import StrEnum

from core.contracts.auth import Principal, Role
from core.contracts.errors import Forbidden


class Permission(StrEnum):
    VALIDATE_PAPER = "validate_paper"


_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.USER: frozenset({Permission.VALIDATE_PAPER}),
    Role.GUEST: frozenset({Permission.VALIDATE_PAPER}),
}


def require(principal: Principal, permission: Permission) -> None:
    granted = any(
        permission in _ROLE_PERMISSIONS.get(role, frozenset()) for role in principal.roles
    )
    if not granted:
        raise Forbidden(
            f"Principal {principal.user_id} (roles={[r.value for r in principal.roles]}) "
            f"lacks permission {permission.value}"
        )
