from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, String
from sqlalchemy import DateTime
from app.time import now


def make_datetime_column() -> Column:
    return Column(DateTime(timezone=True))


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())
    updated_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime


class DocumentBase(SQLModel):
    title: str = Field(default="Untitled Document")
    content: Optional[str] = None
    owner_id: int = Field(foreign_key="user.id", index=True)
    workspace_id: Optional[int] = Field(default=None, foreign_key="workspace.id")


class Document(DocumentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())
    updated_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())


class DocumentCreate(SQLModel):
    title: str = Field(default="Untitled Document")
    workspace_id: Optional[int] = None


class DocumentUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    workspace_id: Optional[int] = None


class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime


class WorkspaceBase(SQLModel):
    name: str


class Workspace(WorkspaceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_by: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())
    updated_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceResponse(WorkspaceBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime


class WorkspaceMemberBase(SQLModel):
    workspace_id: int = Field(foreign_key="workspace.id")
    user_id: int = Field(foreign_key="user.id")
    role: str = Field(default="viewer")  # owner, editor, viewer


class WorkspaceMember(WorkspaceMemberBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    joined_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())


class WorkspaceMemberCreate(SQLModel):
    user_id: int
    role: str = Field(default="viewer")


class WorkspaceMemberResponse(WorkspaceMemberBase):
    id: int
    joined_at: datetime


class DocumentShareBase(SQLModel):
    document_id: int = Field(foreign_key="document.id")
    shared_with_user_id: int = Field(foreign_key="user.id")
    permission: str = Field(default="view")  # view, edit


class DocumentShare(DocumentShareBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    shared_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())


class DocumentShareCreate(SQLModel):
    user_id: int
    permission: str = Field(default="view")


class DocumentShareResponse(DocumentShareBase):
    id: int
    shared_at: datetime


class TokenResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
