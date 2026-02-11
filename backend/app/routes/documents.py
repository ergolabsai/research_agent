# backend/app/routes/documents.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.models import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentShare,
    DocumentShareCreate,
    DocumentShareResponse,
    User,
    Workspace,
    WorkspaceMember,
)
from app.security import get_session, get_current_user_id

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """List all documents owned by the user or shared with them."""
    # Get documents owned by user
    owned_docs = session.exec(
        select(Document).where(Document.owner_id == user_id)
    ).all()

    # Get documents shared with user
    shared_doc_ids = session.exec(
        select(DocumentShare.document_id).where(
            DocumentShare.shared_with_user_id == user_id
        )
    ).all()

    shared_docs = (
        session.exec(select(Document).where(Document.id.in_(shared_doc_ids))).all()
        if shared_doc_ids
        else []
    )

    # Combine and return unique documents
    all_docs = owned_docs + shared_docs
    seen_ids = set()
    unique_docs = []
    for doc in all_docs:
        if doc.id not in seen_ids:
            unique_docs.append(doc)
            seen_ids.add(doc.id)

    return unique_docs


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Get a specific document."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Check if user owns it or has access
    if document.owner_id != user_id:
        share = session.exec(
            select(DocumentShare).where(
                (DocumentShare.document_id == document_id)
                & (DocumentShare.shared_with_user_id == user_id)
            )
        ).first()
        if not share:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    return document


@router.post("", response_model=DocumentResponse)
def create_document(
    doc_create: DocumentCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Create a new document."""
    document = Document(
        title=doc_create.title,
        owner_id=user_id,
        workspace_id=doc_create.workspace_id,
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    doc_update: DocumentUpdate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Update a document. Only the owner can edit, but workspace_id can be updated if user has workspace access."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Only owner can update title/content
    if (doc_update.title is not None or doc_update.content is not None) and document.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can edit document"
        )

    # Check if workspace_id was explicitly provided in the request
    update_data = doc_update.model_dump(exclude_unset=True)
    
    if "workspace_id" in update_data:
        # If setting to a workspace (not null), verify user has access
        if doc_update.workspace_id is not None:
            workspace = session.get(Workspace, doc_update.workspace_id)
            if not workspace:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
            
            # Check if user is owner or member of the workspace
            if workspace.created_by != user_id:
                member = session.exec(
                    select(WorkspaceMember).where(
                        (WorkspaceMember.workspace_id == doc_update.workspace_id)
                        & (WorkspaceMember.user_id == user_id)
                    )
                ).first()
                if not member:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have access to this workspace"
                    )
        
        # Update workspace_id (can be None to remove from workspace)
        document.workspace_id = doc_update.workspace_id

    if doc_update.title is not None:
        document.title = doc_update.title
    if doc_update.content is not None:
        document.content = doc_update.content
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Delete a document."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can delete"
        )

    session.delete(document)
    session.commit()


@router.post("/{document_id}/share", response_model=DocumentShareResponse)
def share_document(
    document_id: int,
    share_create: DocumentShareCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """Share a document with another user."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can share"
        )

    # Check if target user exists
    target_user = session.get(User, share_create.user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if already shared
    existing = session.exec(
        select(DocumentShare).where(
            (DocumentShare.document_id == document_id)
            & (DocumentShare.shared_with_user_id == share_create.user_id)
        )
    ).first()

    if existing:
        # Update permission
        existing.permission = share_create.permission
        session.add(existing)
    else:
        # Create new share
        share = DocumentShare(
            document_id=document_id,
            shared_with_user_id=share_create.user_id,
            permission=share_create.permission,
        )
        session.add(share)

    session.commit()
    return existing or share


@router.delete("/{document_id}/share/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unshare_document(
    document_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user_id: int = Depends(get_current_user_id),
):
    """Unshare a document from a user."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if document.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can unshare"
        )

    share = session.exec(
        select(DocumentShare).where(
            (DocumentShare.document_id == document_id)
            & (DocumentShare.shared_with_user_id == user_id)
        )
    ).first()

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
        )

    session.delete(share)
    session.commit()
