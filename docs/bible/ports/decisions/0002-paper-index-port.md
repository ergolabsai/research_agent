---
id: ports-0002
title: `PaperIndex` port for local paper corpus search
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

See [capabilities/knowledge/0002 — Paper index is exposed via a port](../../capabilities/knowledge/decisions/0002-knowledge-store-port.md) for the motivation. This ADR is the port's catalog entry.

## Decision

```python
class SearchMode(str, Enum):
    VECTOR = "vector"
    FULL_TEXT = "full_text"
    HYBRID = "hybrid"

class PaperIndex(Protocol):
    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        mode: SearchMode = SearchMode.HYBRID,
        filters: PaperFilters | None = None,
    ) -> list[Paper]: ...

    async def get(self, paper_id: PaperId) -> Paper | None: ...

    async def ingest(self, papers: Sequence[Paper]) -> None: ...
```

`Paper`, `PaperId`, and `PaperFilters` are contract types defined in `core/contracts/paper.py`. `PaperFilters` is a small structured value (year range, venue, etc.) — not a free-form query string, to avoid leaking adapter query languages.

## Consequences

**Easy:**
- The Librarian and any other consumer code call port methods. The adapter handles connection pooling, table caching, and embedding generation.
- Vector store swap (LanceDB → pgvector → Qdrant) is an adapter swap.
- Test fakes are tiny: a dict of paper-id → Paper, with `search` doing substring matching.

**Hard:**
- The `filters` shape must be expressive enough for real queries (year, venue, author) without becoming a hidden query DSL. Start small; add fields when use-cases demand them.
- Ingestion is async-write; bulk ingestion at scale may want streaming. The current single `ingest(Sequence[Paper])` is acceptable for batch sizes the system handles today (thousands at a time, not millions).

**Forecloses:**
- Free-form query strings that pass through the port to the adapter (e.g., `query="title:foo AND year:>2020"`). Filters go in the typed `PaperFilters`.

## Adapters

- **`LanceDBPaperIndex`** — current. Embedding via the configured model (HuggingFace), full-text via LanceDB's FTS, hybrid via the adapter's reranking.
- **`InMemoryPaperIndex`** — test-only fake. Dictionary-backed.
- **`PgvectorPaperIndex`** — proposed; deferred until a forcing function appears (operational pressure to consolidate stores).

See [adapters/driven/decisions/0003-lancedb-paper-index.md](../../adapters/driven/decisions/0003-lancedb-paper-index.md).

## Review trigger

- A filter the system needs cannot be expressed in `PaperFilters` cleanly. Add a field; resist a free-form query string.
- Embedding refresh (re-embedding the entire corpus when the embedding model changes) becomes a frequent operation; may warrant a `reembed` port method.
- Ingestion volumes grow past what `Sequence[Paper]` can hold in memory; introduce a streaming-ingestion method.
