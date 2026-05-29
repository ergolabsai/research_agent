# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""LanceDBPaperIndex — adapter satisfying `core.ports.paper_index.PaperIndex`.

Delegates to the free functions in `advisor_pipeline/utils/lancedb_search.py`
which currently own the module-level `_db_connection` / `_table` globals.
Step 5 moves that state onto this adapter instance and deletes the globals.

The lancedb_search module does an eager `import torch` at module top.
Importing this adapter at container construction time should not pay that
cost on environments where torch is absent (e.g. the API process when the
pipeline hasn't run yet), so imports happen inside the methods.
"""

import pandas as pd


class LanceDBPaperIndex:
    """Satisfies `PaperIndex` by delegating to `lancedb_search` helpers."""

    def vector_search(self, query: str, limit: int = 10) -> pd.DataFrame:
        from advisor_pipeline.utils.lancedb_search import vector_search

        return vector_search(query, limit=limit)

    def fts_search(self, query: str, limit: int = 10) -> pd.DataFrame:
        from advisor_pipeline.utils.lancedb_search import fts_search

        return fts_search(query, limit=limit)
