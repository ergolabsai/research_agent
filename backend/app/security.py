# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

# backend/app/security.py
import json
from sqlmodel import create_engine, Session
from fastapi import HTTPException, status, Header
import bcrypt
import pyseto
from pyseto import Key
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from advisor_pipeline.config.settings import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

# Lazily initialised on first request so startup order doesn't matter.
_paseto_verify_key: Key | None = None


def _get_verify_key() -> Key:
    global _paseto_verify_key
    if _paseto_verify_key is None:
        pub = load_pem_public_key(settings.paseto_public_key.encode())
        _paseto_verify_key = Key.new(version=4, purpose="public", key=pub)
    return _paseto_verify_key


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_token(token: str) -> int | None:
    try:
        decoded = pyseto.decode(_get_verify_key(), token, deserializer=json)
        return int(decoded.payload["sub"])
    except (pyseto.PasetoError, KeyError, ValueError, TypeError):
        return None


def get_current_user_id(authorization: str = Header(None)) -> int:
    """Extract and verify user ID from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return user_id


def get_session():
    with Session(engine) as session:
        yield session
