# backend/app/security.py
from datetime import timedelta, timezone
from typing import Optional
from sqlmodel import create_engine, Session
from jose import JWTError, jwt
from fastapi import HTTPException, status, Header
import bcrypt
import os
from app.time import APP_TIMEZONE, now
from advisor_pipeline.config.settings import settings

# Security configuration
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

if not os.path.exists("data"):
    os.makedirs("data")
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    # Convert sub to string as required by PyJWT
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = now() + expires_delta
    else:
        expire = now() + timedelta(minutes=15)
    to_encode.update({"exp": expire.astimezone(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    # Convert sub to string as required by PyJWT
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    expire = now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire.astimezone(timezone.utc), "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        user_id = int(sub)
        return user_id
    except JWTError:
        return None
    except (ValueError, TypeError):
        return None


def get_current_user_id(authorization: str = Header(None)) -> int:
    """Extract and verify user ID from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return user_id


def get_session():
    with Session(engine) as session:
        yield session
