---
id: capabilities-knowledge-0002
title: Paper index is exposed via a port, not the LanceDB API directly
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Today, the `Librarian` agent and several utilities reach directly into `lancedb` — opening connections, calling LanceDB-specific APIs, and assuming the table schema. This is the most common kind of leak in a pre-hexagonal codebase: the implementation detail of *which vector store* leaks through dependencies into agents that should not care.

The leak is a problem for three reasons:

1. Swapping LanceDB for another vector store (pgvector, Qdrant, Weaviate) would require changes in every agent that calls it.
2. Tests must either spin up a real LanceDB or monkey-patch the import — neither is fast or clean.
3. The agents' shape is constrained by LanceDB's API surface (`Table.search(...).where(...).limit(...)`) rather than by what the agent actually needs.

## Decision

A `PaperIndex` port is declared in `core/ports/paper_index.py`. It expresses what the *use-cases and services* need, not what the *vector store* offers:

```python
class PaperIndex(Protocol):
    async def search(self, query: str, *, limit: int, mode: SearchMode = SearchMode.HYBRID) -> list[Paper]: ...
    async def get(self, paper_id: PaperId) -> Paper | None: ...
    async def ingest(self, papers: Sequence[Paper]) -> None: ...
```

LanceDB is the *current* implementation, provided by a driven adapter (`adapters/driven/paper_index/lancedb.py`). The adapter knows about LanceDB; the port and its callers do not.

## Consequences

**Easy:**
- The `Librarian` (a core service) takes a `PaperIndex` in its constructor and calls only the port methods. It is testable with an in-memory fake.
- A future swap to pgvector is a new adapter + a composition-layer change. Use-cases do not move.
- The port surface is small and explicit. New requirements ("filter by year") get added consciously, not by leaking yet another LanceDB method.

**Hard:**
- The current LanceDB-specific call sites must be refactored: each direct LanceDB call becomes a method call on an injected port. This is the work that breaks the import-level coupling.
- The port may need to evolve (new methods, new filter parameters) as use-cases grow. Each evolution is a deliberate design pass, not an accidental method chain.

**Forecloses:**
- "Just call `lancedb.connect()` from inside the agent." Not anymore — the agent receives `PaperIndex`.
- LanceDB-specific advanced features (e.g., FTS-and-vector-fused ranking with custom weights) bleeding into agent code. If the use-case needs it, the port surfaces it; the adapter implements it.

## Alternatives considered

- **Keep direct LanceDB calls but wrap them in a "search helper" module in core** — rejected. A helper module still imports LanceDB into core, breaching [architecture/0003](../../../architecture/decisions/0003-core-has-no-io.md). The port is the right answer.
- **A more elaborate port with many query primitives** — rejected. The port surfaces what use-cases need; speculative methods go in as use-cases require them.
- **No port, but a façade in adapters/** — rejected. Without a Protocol in core, the use-case has no type to declare. The port is what makes the use-case's dependency declarable.

## Review trigger

- A query pattern needed by a use-case cannot be expressed against the port without leaking adapter specifics into method parameters. At that point reshape the port; if the reshape is infeasible, the adapter is not generic enough and a second port (or a layered port) may be needed.
