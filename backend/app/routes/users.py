# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

# backend/app/routes/users.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.models import User, UserResponse
from app.security import get_session

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/search", response_model=list[UserResponse])
def search_users(q: str, session: Session = Depends(get_session)):
    if not q or len(q) < 2:
        return []

    users = session.exec(
        select(User).where(
            (User.email.ilike(f"%{q}%")) |
            (User.username.ilike(f"%{q}%"))
        ).limit(10)
    ).all()

    return users
