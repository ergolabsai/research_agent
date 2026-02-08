from fastapi import APIRouter, Depends, HTTPException, status, Header, Response, Request
from sqlmodel import Session, select
from datetime import timedelta, datetime
from pydantic import BaseModel
import secrets
import uuid
from app.models import (
    User, UserCreate, UserResponse, TokenResponse
)
from app.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_session,
    get_current_user_id, REFRESH_TOKEN_EXPIRE_DAYS
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    identifier: str  # Can be email or username
    password: str


@router.post("/register", response_model=TokenResponse)
def register(
    user_create: UserCreate,
    response: Response,
    session: Session = Depends(get_session),
    authorization: str | None = Header(None),
):
    # If a guest is authenticated, convert the existing account instead of creating a new one.
    guest_user = None
    if authorization:
        try:
            scheme, token = authorization.split(" ")
            if scheme.lower() == "bearer":
                user_id = verify_token(token)
                if user_id:
                    candidate = session.get(User, user_id)
                    if candidate and (
                        candidate.email.startswith("guest+")
                        or candidate.username.startswith("guest_")
                    ):
                        guest_user = candidate
        except ValueError:
            guest_user = None

    # Check for email/username collisions.
    existing_email = session.exec(
        select(User).where(User.email == user_create.email)
    ).first()
    if existing_email and (not guest_user or existing_email.id != guest_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    existing_username = session.exec(
        select(User).where(User.username == user_create.username)
    ).first()
    if existing_username and (not guest_user or existing_username.id != guest_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    hashed_password = get_password_hash(user_create.password)

    if guest_user:
        guest_user.email = user_create.email
        guest_user.username = user_create.username
        guest_user.hashed_password = hashed_password
        guest_user.updated_at = datetime.now()
        session.add(guest_user)
        session.commit()
        session.refresh(guest_user)
        user = guest_user
    else:
        # Create new user
        user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    # Generate tokens
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.id})

    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert days to seconds
        httponly=True,
        secure=True,  # Should be True in production with HTTPS
        samesite="lax"
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/try", response_model=TokenResponse)
def try_it_now(response: Response, session: Session = Depends(get_session)):
    guest_suffix = uuid.uuid4().hex[:12]
    guest_email = f"guest+{guest_suffix}@try.me"
    guest_username = f"guest_{guest_suffix[:8]}"
    guest_password = secrets.token_urlsafe(24)

    user = User(
        email=guest_email,
        username=guest_username,
        hashed_password=get_password_hash(guest_password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.id})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenResponse)
def login(login_request: LoginRequest, response: Response, session: Session = Depends(get_session)):
    # Find user by email or username
    user = session.exec(
        select(User).where(
            (User.email == login_request.identifier) |
            (User.username == login_request.identifier)
        )
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email, username, or password"
        )
    
    # Verify password
    password_match = verify_password(login_request.password, user.hashed_password)
    
    if not password_match:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email, username, or password"
        )

    # Generate tokens
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.id})

    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert days to seconds
        httponly=True,
        secure=True,  # Should be True in production with HTTPS
        samesite="lax"
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, session: Session = Depends(get_session)):
    # Read refresh token from HTTP-only cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookies"
        )
    
    user_id = verify_token(refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = create_refresh_token(data={"sub": user.id})

    # Set new refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert days to seconds
        httponly=True,
        secure=True,  # Should be True in production with HTTPS
        samesite="lax"
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


@router.get("/me", response_model=UserResponse)
def get_current_user(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user

@router.post("/logout")
def logout(response: Response):
    """Clear the refresh token cookie."""
    response.delete_cookie(key="refresh_token", httponly=True, secure=True, samesite="lax")
    return {"message": "Logged out successfully"}