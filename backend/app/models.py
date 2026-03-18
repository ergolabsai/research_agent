# backend/app/models.py
from datetime import datetime
from typing import Optional
from sqlmodel import Relationship, SQLModel, Field, Column
from sqlalchemy import DateTime, Text
from app.time import now


def make_datetime_column() -> Column:
    return Column(DateTime(timezone=True))


# --- User ---

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


# --- Document ---

class DocumentBase(SQLModel):
    title: str = Field(default="Untitled Document")
    content: Optional[str] = Field(default=None)
    owner_id: int = Field(foreign_key="user.id", index=True)
    workspace_id: Optional[int] = Field(default=None, foreign_key="workspace.id")


class Document(DocumentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())
    updated_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())
    attachments: list["Attachment"] = Relationship(back_populates="document")


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


# --- Attachment ---

class AttachmentBase(SQLModel):
    document_id: int = Field(foreign_key="document.id", index=True)
    filename: str                        # original filename, e.g. "photo.png"
    object_key: str                      # MinIO path, e.g. "documents/42/uuid.png"
    content_type: str                    # MIME type, e.g. "image/png"
    size: int                            # bytes


class Attachment(AttachmentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())
    document: Optional[Document] = Relationship(back_populates="attachments")


class AttachmentCreate(SQLModel):
    filename: str
    content_type: str
    size: int


class AttachmentRead(SQLModel):
    id: int
    filename: str
    object_key: str
    content_type: str
    size: int
    created_at: datetime


# --- Pipeline Job ---

class PipelineJob(SQLModel, table=True):
    """Persistent record of a pipeline validation job."""

    __tablename__ = "pipeline_job"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    paper_id: str = Field(index=True)
    title: str
    status: str = Field(default="pending")  # pending, running, completed, failed
    current_step: int = Field(default=0)
    total_steps: int = Field(default=8)
    step_name: str = Field(default="")
    error: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Full paper context stored for reproducibility
    paper_text: Optional[str] = Field(default=None, sa_column=Column(Text))
    bibliography_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    figures_json: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Final results (JSON-serialized)
    result_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    graph_json: Optional[str] = Field(default=None, sa_column=Column(Text))

    created_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))

    step_logs: list["PipelineStepLog"] = Relationship(back_populates="job")


class PipelineStepLog(SQLModel, table=True):
    """Log entry for each pipeline step, storing full agent output for transparency."""

    __tablename__ = "pipeline_step_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(foreign_key="pipeline_job.job_id", index=True)
    step_name: str = Field(index=True)
    step_number: int
    status: str = Field(default="completed")  # running, completed, failed

    # Agent outputs as JSON — schema varies by step
    # make_context: { enriched_context }
    # gather_papers: { search_queries, related_papers[], context_summary }
    # map_logic: { paper_structure }
    # find_evidence: { step_evidence[] }
    # evaluate_figures: { figure_evaluations[] }
    # evaluate_math: { math_evaluations[] }
    # score_papers: { scored_papers[], librarian_statistics }
    # compile_results: { validation_result, confidence_score }
    output_json: Optional[str] = Field(default=None, sa_column=Column(Text))

    # LLM prompts sent during this step (for fine-tuning transparency)
    prompts_json: Optional[str] = Field(default=None, sa_column=Column(Text))

    started_at: datetime = Field(default_factory=now, sa_column=make_datetime_column())
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    duration_seconds: Optional[float] = Field(default=None)

    job: Optional["PipelineJob"] = Relationship(back_populates="step_logs")


# --- Workspace ---

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


# --- Tokens ---

class TokenResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
