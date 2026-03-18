"""
SQLite Configuration and Connection Management for the Calculator Server.

Uses the same SQLite database as the backend (via ``settings.database_url``).
"""
from sqlmodel import SQLModel, Session, create_engine

from advisor_pipeline.config.settings import settings

# Lazy singleton engine – created once per process.
_engine = None


def get_engine():
    """Return (and cache) a SQLAlchemy engine for the shared SQLite DB."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_session():
    """Yield a SQLModel Session scoped to the shared engine."""
    with Session(get_engine()) as session:
        yield session


def init_db():
    """Create all SQLModel tables (including Formula) if they don't exist."""
    from .models import Formula  # noqa: F401 – registers the table
    SQLModel.metadata.create_all(get_engine())
