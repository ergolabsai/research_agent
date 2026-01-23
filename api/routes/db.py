# api/routes/db.py
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, create_engine, SQLModel, Field, select
from typing import Optional, List
import dotenv
dotenv.load_dotenv()

# ---------- Models ----------

class DocumentBase(SQLModel):
    content: str

class Document(DocumentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

# ---------- DB setup ----------

engine = create_engine(
    os.getenv("DATABASE_URL", "sqlite:///./dev.db"),
    connect_args={"check_same_thread": False},
)

SQLModel.metadata.create_all(engine)

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session


# ---------- Routes ------------
@router.post("/docs/new", response_model=Document)
def create_doc(
    doc: DocumentBase,
    session: Session = Depends(get_session),
):
    db_doc = Document.model_validate(doc)
    session.add(db_doc)
    session.commit()
    session.refresh(db_doc)
    return db_doc

@router.get("/docs", response_model=List[Document])
def list_docs(session: Session = Depends(get_session)):
    docs = session.exec(select(Document)).all()
    return docs

@router.get("/docs/{doc_id}", response_model=Document)
def get_doc(
    doc_id: int,
    session: Session = Depends(get_session),
):
    db_doc = session.get(Document, doc_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_doc

@router.patch("/docs/{doc_id}", response_model=Document)
def update_doc(
    doc_id: int,
    doc_update: DocumentBase,
    session: Session = Depends(get_session),
):
    db_doc = session.get(Document, doc_id)
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = doc_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_doc, key, value)

    session.add(db_doc)
    session.commit()
    session.refresh(db_doc)
    return db_doc