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
from adapters.driven.identity.paseto_token_issuer import PasetoTokenIssuer
from adapters.driven.repositories.sqlite_user_repository import SqliteUserRepository
from advisor_pipeline.config.settings import settings
from app.security import get_session
from core.ports.token_issuer import TokenIssuer
from core.use_cases.identity.login_user import LoginUser
from core.use_cases.identity.register_user import RegisterUser

# Singletons — stateless, safe to reuse across requests.
_password_hasher = BcryptPasswordHasher(work_factor=12)
_token_issuer: PasetoTokenIssuer | None = None


def get_token_issuer() -> TokenIssuer:
    """FastAPI dependency that returns the shared token issuer.

    Lazily initialised so that importing this module in tests does not require
    PASETO keys to be configured in the environment.
    """
    global _token_issuer
    if _token_issuer is None:
        if not settings.paseto_private_key or not settings.paseto_public_key:
            raise RuntimeError(
                "PASETO_PRIVATE_KEY and PASETO_PUBLIC_KEY must be set in the environment.\n"
                "Generate a key pair with:\n"
                "  openssl genpkey -algorithm ed25519 -out ed25519_private.pem\n"
                "  openssl pkey -in ed25519_private.pem -pubout -out ed25519_public.pem"
            )
        _token_issuer = PasetoTokenIssuer(
            private_key_pem=settings.paseto_private_key,
            public_key_pem=settings.paseto_public_key,
        )
    return _token_issuer


def get_login_user(session: Session = Depends(get_session)) -> LoginUser:
    """FastAPI dependency that builds a LoginUser use case for the current request."""
    return LoginUser(
        user_repo=SqliteUserRepository(session),
        password_hasher=_password_hasher,
        token_issuer=get_token_issuer(),
    )


def get_register_user(session: Session = Depends(get_session)) -> RegisterUser:
    """FastAPI dependency that builds a RegisterUser use case for the current request."""
    return RegisterUser(
        user_repo=SqliteUserRepository(session),
        password_hasher=_password_hasher,
        token_issuer=get_token_issuer(),
    )
