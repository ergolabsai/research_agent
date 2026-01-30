from fastapi import APIRouter, Depends, HTTPException, status, Header, Response, Request
from sqlmodel import Session, select
from datetime import timedelta
from pydantic import BaseModel
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
def register(user_create: UserCreate, response: Response, session: Session = Depends(get_session)):
    # Check if user exists
    existing = session.exec(
        select(User).where(User.email == user_create.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_create.password)
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