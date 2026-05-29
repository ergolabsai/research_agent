# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Composition root: instantiates adapters and wires them into use cases.

This is the only module allowed to import from both core and adapters.
Nothing in core or adapters imports from here.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from adapters.driven.identity.bcrypt_password_hasher import BcryptPasswordHasher
from adapters.driven.identity.paseto_token_issuer import PasetoTokenIssuer
from adapters.driven.job_store.legacy_sqlite import LegacyJobStore
from adapters.driven.llm.anthropic import ChatLLMClient
from adapters.driven.mcp.calculator_client import McpCalculatorClient
from adapters.driven.paper_index.lancedb import LanceDBPaperIndex
from adapters.driven.pipeline_runner.legacy import LegacyPipelineRunner
from adapters.driven.repositories.sqlite_user_repository import SqliteUserRepository
from advisor_pipeline.config.settings import settings
from app.security import get_session
from core.contracts.auth import Principal, UserId
from core.contracts.errors import ExpiredToken, InvalidToken
from core.ports.token_issuer import TokenIssuer
from core.use_cases.identity.get_current_user import GetCurrentUser
from core.use_cases.identity.login_user import LoginUser
from core.use_cases.identity.refresh_access_token import RefreshAccessToken
from core.use_cases.identity.register_user import RegisterUser
from core.use_cases.validation.validate_paper import ValidatePaper

# Singletons — stateless, safe to reuse across requests.
_password_hasher = BcryptPasswordHasher(work_factor=12)
_token_issuer: PasetoTokenIssuer | None = None

# Pipeline-side adapters. Constructed eagerly so a misconfigured environment
# surfaces at startup, not on the first /api/pipeline/validate request. Not
# injected anywhere yet — Step 1 of the migration wires these into the
# orchestrator and agents. `McpCalculatorClient` is the class itself (not an
# instance) because each pipeline run opens its own MCP session via
# `with McpCalculatorClient() as client:`.
_llm_client = ChatLLMClient()
_paper_index = LanceDBPaperIndex()
_calculator_cls = McpCalculatorClient


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


async def get_principal(
    authorization: str | None = Header(None),
    token_issuer: TokenIssuer = Depends(get_token_issuer),
) -> Principal:
    """FastAPI dependency that resolves the authenticated caller's Principal.

    Verifies the bearer access token and builds the Principal from its claims.
    Raises 401 on any failure — missing header, malformed scheme, expired or invalid token.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        scheme, token = authorization.split(" ", 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    try:
        claims = await token_issuer.verify_access_token(token)
    except (ExpiredToken, InvalidToken):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return Principal(
        user_id=UserId(int(claims.sub)),
        email=claims.email,
        roles=claims.roles,
        is_guest=claims.is_guest,
    )


def get_current_user(
    session: Session = Depends(get_session),
) -> GetCurrentUser:
    """FastAPI dependency that builds a GetCurrentUser use case for the current request."""
    return GetCurrentUser(user_repo=SqliteUserRepository(session))


def get_validate_paper(
    session: Session = Depends(get_session),
) -> ValidatePaper:
    """FastAPI dependency that builds a ValidatePaper use case for the current request."""
    return ValidatePaper(
        job_store=LegacyJobStore(session),
        pipeline_runner=LegacyPipelineRunner(),
    )


def get_refresh_access_token(
    session: Session = Depends(get_session),
) -> RefreshAccessToken:
    """FastAPI dependency that builds a RefreshAccessToken use case for the current request."""
    return RefreshAccessToken(
        user_repo=SqliteUserRepository(session),
        token_issuer=get_token_issuer(),
    )
