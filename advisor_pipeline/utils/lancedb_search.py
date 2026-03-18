"""Shared LanceDB search utilities.

Provides vector search and full-text search against the arXiv papers table.
Used by the Librarian agent and the Streamlit navigator.
"""

import os
from functools import lru_cache

import lancedb
import pandas as pd
import torch
from lancedb.embeddings import get_registry
from advisor_pipeline.config.settings import settings

_db_connection = None
_table = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LANCEDB_PATH = settings.LANCEDB_PATH
EMBEDDING_MODEL = settings.EMBEDDING_MODEL
TABLE_NAME = "papers"


# ---------------------------------------------------------------------------
# Initialisation (lazy singletons)
# ---------------------------------------------------------------------------

def _get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def get_embed_func():
    """Return the HuggingFace embedding function (cached singleton)."""
    device = _get_device()
    return get_registry().get("huggingface").create(name=EMBEDDING_MODEL, device=device)


def connect(db_path: str | None = None) -> lancedb.DBConnection:
    """Return a cached LanceDB connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = lancedb.connect(db_path or LANCEDB_PATH)
    return _db_connection


def open_table(db_path: str | None = None, table_name: str | None = None):
    """Return a cached LanceDB table handle."""
    global _table
    if _table is None:
        db = connect(db_path)
        _table = db.open_table(table_name or TABLE_NAME)
    return _table


# ---------------------------------------------------------------------------
# Search functions
# ---------------------------------------------------------------------------

def vector_search(query: str, limit: int = 10, db_path: str | None = None) -> pd.DataFrame:
    """Embed *query* and perform vector-similarity search.

    Returns a DataFrame with columns from the papers table plus ``_distance``
    (lower = more similar).
    """
    tbl = open_table(db_path)
    embed = get_embed_func()
    query_vector = embed.compute_query_embeddings([query])[0]
    results = tbl.search(query_vector).limit(limit).to_pandas()
    return results


def fts_search(query: str, limit: int = 10, db_path: str | None = None) -> pd.DataFrame:
    """Full-text search over title + abstract (tantivy index).

    Returns a DataFrame with columns from the papers table plus ``_score``
    (higher = more relevant).  Returns an empty DataFrame when nothing matches.
    """
    tbl = open_table(db_path)
    results = tbl.search(query).limit(limit).to_pandas()
    if results.empty:
        return pd.DataFrame()
    return results
