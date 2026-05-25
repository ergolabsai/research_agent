# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

# backend/app/routes/auth.py
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, Request, Header, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.models import User, UserCreate, UserResponse, TokenResponse
from app.security import (
    get_session, get_current_user_id, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS,
)
from composition.container import (
    get_login_user,
    get_refresh_access_token,
    get_register_user,
    get_token_issuer,
)
from core.contracts.auth import Principal, Role, UserId
from core.contracts.errors import DuplicateEmail, DuplicateUsername, ExpiredToken, InvalidCredentials, InvalidToken
from core.contracts.tokens import TokenClaims
from core.ports.token_issuer import TokenIssuer
from core.use_cases.identity.login_user import LoginUser, LoginUserRequest
from core.use_cases.identity.refresh_access_token import (
    RefreshAccessToken,
    RefreshAccessTokenRequest,
)
from core.use_cases.identity.register_user import RegisterUser, RegisterUserRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1)
    password: str = Field(min_length=1)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite="lax",
    )


async def _resolve_guest_principal(
    authorization: str | None, token_issuer: TokenIssuer
) -> Principal | None:
    """Return a guest Principal if the caller holds a valid guest PASETO token, else None."""
    if not authorization:
        return None
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            return None
        claims = await token_issuer.verify_access_token(token)
        if not claims.is_guest:
            return None
        return Principal(
            user_id=UserId(int(claims.sub)),
            email=claims.email,
            roles=[Role.GUEST],
            is_guest=True,
        )
    except (ValueError, ExpiredToken, InvalidToken):
        return None


@router.post("/register", response_model=TokenResponse)
async def register(
    user_create: UserCreate,
    response: Response,
    authorization: str | None = Header(None),
    register_user: RegisterUser = Depends(get_register_user),
    token_issuer: TokenIssuer = Depends(get_token_issuer),
):
    principal = await _resolve_guest_principal(authorization, token_issuer)

    try:
        result = await register_user.execute(
            principal,
            RegisterUserRequest(
                email=user_create.email,
                username=user_create.username,
                password=user_create.password,
            ),
        )
    except DuplicateEmail:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except DuplicateUsername:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    _set_refresh_cookie(response, result.refresh_token.token)
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token.token,
    )


@router.post("/try", response_model=TokenResponse)
async def try_it_now(
    response: Response,
    session: Session = Depends(get_session),
    token_issuer: TokenIssuer = Depends(get_token_issuer),
):
    guest_suffix = uuid.uuid4().hex[:12]
    user = User(
        email=f"guest+{guest_suffix}@try.me",
        username=f"guest_{guest_suffix[:8]}",
        hashed_password="!",  # unusable sentinel — guests authenticate via tokens only
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    now = datetime.now(timezone.utc)
    claims = TokenClaims(
        sub=str(user.id),
        email=user.email,
        roles=[Role.GUEST],
        is_guest=True,
        iat=now,
        exp=now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    access_token = await token_issuer.mint_access_token(claims)
    refresh = await token_issuer.mint_refresh_token(UserId(user.id))

    _set_refresh_cookie(response, refresh.token)
    return TokenResponse(access_token=access_token, refresh_token=refresh.token)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_request: LoginRequest,
    response: Response,
    login_user: LoginUser = Depends(get_login_user),
):
    try:
        result = await login_user.execute(
            LoginUserRequest(
                identifier=login_request.identifier,
                password=login_request.password,
            )
        )
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email, username, or password",
        )

    _set_refresh_cookie(response, result.refresh_token.token)
    return TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token.token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    refresh_access_token: RefreshAccessToken = Depends(get_refresh_access_token),
):
    refresh_token_str = request.cookies.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookies",
        )

    try:
        result = await refresh_access_token.execute(
            RefreshAccessTokenRequest(refresh_token=refresh_token_str)
        )
    except ExpiredToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    _set_refresh_cookie(response, result.refresh_token.token)
    return TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token.token)


@router.get("/me", response_model=UserResponse)
def get_current_user(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@router.post("/logout")
def logout(response: Response):
    """Clear the refresh token cookie."""
    response.delete_cookie(key="refresh_token", httponly=True, secure=True, samesite="lax")
    return {"message": "Logged out successfully"}
