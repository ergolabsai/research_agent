---
id: adapters-driven-0003
title: LanceDB as the `PaperIndex` adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

`PaperIndex` requires vector search, full-text search, and hybrid ranking over a paper corpus (~2M arXiv papers). Several vector stores are viable: LanceDB, pgvector (Postgres extension), Qdrant, Weaviate, Milvus. They differ along: embedding-model integration, hybrid-search support, operational complexity, and pre-alpha vs production fit.

## Decision

Implement `PaperIndex` with a `LanceDBPaperIndex` adapter. LanceDB was selected for:

- **Embedded operation** — no separate service to run in dev or pre-alpha.
- **Native hybrid search** — vector + full-text + reranking in one query.
- **Pandas-compatible API** — easy to script ingestion and inspection.
- **Embedding registry** — model is configured once; the adapter handles embedding generation.

Current implementation: `advisor_pipeline/utils/lancedb_search.py` (will move to `adapters/driven/paper_index/lancedb.py`).

The adapter caches the connection and table handle at construction (one connection per process) — see the existing `connect()` / `open_table()` helpers.

## Consequences

**Easy:**
- Zero ops overhead in dev. The vector store is a directory of files.
- Hybrid search works out of the box.
- Embedding-model swaps are configured in the adapter, not in the calling agents.

**Hard:**
- Single-writer model. Concurrent ingest from multiple processes requires care (file-locking). Acceptable for the current ingestion pattern (a periodic batch job, not live multi-writer).
- Storage scales with corpus size. ~2M arXiv papers fits comfortably on a single dedicated server; growing past 10M may require partitioning or a different store.
- LanceDB is younger than Postgres-based alternatives. Operational maturity is improving but not at the level of pgvector.

**Forecloses:**
- Multi-writer concurrent ingestion without process coordination.
- Querying across multiple corpora joined by SQL semantics. The adapter exposes the port's narrow surface; cross-corpus joins are a use-case concern.

## Alternatives considered

- **pgvector** — viable; preferred if the system already runs Postgres. Postgres is on the migration roadmap (Step 3) but for jobs/users, not the paper corpus — keeping the corpus on LanceDB is simpler.
- **Qdrant** — viable; requires running Qdrant as a service. Adds ops surface in pre-alpha that LanceDB does not.
- **Weaviate / Milvus** — overpowered for the corpus size and team size.

## Review trigger

- The corpus outgrows LanceDB's single-machine comfort zone (~10M+ papers, or concurrent multi-writer ingestion).
- An operational requirement to host the index in the same store as relational data appears — at that point pgvector becomes attractive.
- LanceDB's API stability becomes a recurring upgrade pain.
