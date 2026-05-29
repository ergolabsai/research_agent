# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""PaperIndex port.

Replaces direct imports of `vector_search` / `fts_search` from
`advisor_pipeline/utils/lancedb_search.py` (which holds module-level
`_db_connection` / `_table` globals). The concrete LanceDB adapter and any
future hosted vector DB satisfy this surface.

Return type is `pandas.DataFrame` to match the current Librarian call sites
(librarian.py:143, librarian.py:219), which then feed
`_lancedb_rows_to_related`. Tightening to a domain-shaped row type belongs
with the librarian rewrite in Step 1, not at port-definition time.
"""

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class PaperIndex(Protocol):
    def vector_search(self, query: str, limit: int = 10) -> pd.DataFrame:
        """Embed *query* and return vector-similarity hits.

        DataFrame columns mirror the underlying papers table plus a
        ``_distance`` column (lower = more similar).
        """
        ...

    def fts_search(self, query: str, limit: int = 10) -> pd.DataFrame:
        """Full-text search over title + abstract.

        DataFrame columns mirror the underlying papers table plus a
        ``_score`` column (higher = more relevant). Empty DataFrame on no
        match.
        """
        ...
