from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.models import (
    Workspace,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceMember,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    Document,
    User,
)
from app.security import get_session, get_current_user_id

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """List all workspaces the user is a member of or owns."""
    # Get workspaces created by user
    owned = session.exec(
        select(Workspace).where(Workspace.created_by == user_id)
    ).all()

    # Get workspaces where user is a member
    member_workspace_ids = session.exec(
        select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == user_id
        )
    ).all()

    member_workspaces = (
        session.exec(select(Workspace).where(Workspace.id.in_(member_workspace_ids))).all()
        if member_workspace_ids
        else []
    )

    # Combine and return unique workspaces
    all_workspaces = owned + member_workspaces
    seen_ids = set()
    unique_workspaces = []
    for ws in all_workspaces:
        if ws.id not in seen_ids:
            unique_workspaces.append(ws)
            seen_ids.add(ws.id)

    return unique_workspaces


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Get a specific workspace."""
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    # Check if user is owner or member
    if workspace.created_by != user_id:
        member = session.exec(
            select(WorkspaceMember).where(
                (WorkspaceMember.workspace_id == workspace_id)
                & (WorkspaceMember.user_id == user_id)
            )
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    return workspace


@router.post("", response_model=WorkspaceResponse)
def create_workspace(
    ws_create: WorkspaceCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Create a new workspace."""
    workspace = Workspace(name=ws_create.name, created_by=user_id)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Delete a workspace and all its documents."""
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    if workspace.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only creator can delete"
        )

    # Delete all documents in workspace
    documents = session.exec(
        select(Document).where(Document.workspace_id == workspace_id)
    ).all()
    for doc in documents:
        session.delete(doc)

    # Delete all members
    members = session.exec(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    ).all()
    for member in members:
        session.delete(member)

    # Delete workspace
    session.delete(workspace)
    session.commit()


@router.get("/{workspace_id}/documents", response_model=List)
def get_workspace_documents(
    workspace_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Get all documents in a workspace."""
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    # Check if user has access
    if workspace.created_by != user_id:
        member = session.exec(
            select(WorkspaceMember).where(
                (WorkspaceMember.workspace_id == workspace_id)
                & (WorkspaceMember.user_id == user_id)
            )
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    documents = session.exec(
        select(Document).where(Document.workspace_id == workspace_id)
    ).all()
    return documents


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse)
def add_workspace_member(
    workspace_id: int,
    member_create: WorkspaceMemberCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Add a member to a workspace."""
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    if workspace.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only creator can add members"
        )

    # Check if target user exists
    target_user = session.get(User, member_create.user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if already a member
    existing = session.exec(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == workspace_id)
            & (WorkspaceMember.user_id == member_create.user_id)
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member"
        )

    # Add member
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=member_create.user_id,
        role=member_create.role,
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_workspace_member(
    workspace_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """Remove a member from a workspace."""
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    if workspace.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only creator can remove members"
        )

    member = session.exec(
        select(WorkspaceMember).where(
            (WorkspaceMember.workspace_id == workspace_id)
            & (WorkspaceMember.user_id == user_id)
        )
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    session.delete(member)
    session.commit()
