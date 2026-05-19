# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Composition root: instantiates adapters and wires them into use cases.

This is the only module allowed to import from both core and adapters.
Nothing in core or adapters imports from here.
"""

from fastapi import Depends
from sqlmodel import Session

from adapters.driven.identity.bcrypt_password_hasher import BcryptPasswordHasher
from adapters.driven.identity.jose_token_issuer import JoseTokenIssuer
from adapters.driven.repositories.sqlite_user_repository import SqliteUserRepository
from advisor_pipeline.config.settings import settings
from app.security import get_session
from core.use_cases.identity.register_user import RegisterUser

# Singletons — stateless, safe to reuse across requests.
_password_hasher = BcryptPasswordHasher(work_factor=12)
_token_issuer = JoseTokenIssuer(secret_key=settings.secret_key)


def get_register_user(session: Session = Depends(get_session)) -> RegisterUser:
    """FastAPI dependency that builds a RegisterUser use case for the current request."""
    return RegisterUser(
        user_repo=SqliteUserRepository(session),
        password_hasher=_password_hasher,
        token_issuer=_token_issuer,
    )