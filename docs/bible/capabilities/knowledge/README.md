# Capability: Knowledge

Knowledge is the system's view of *what scientific papers exist in the world*. It maintains a searchable index and serves lookups for the [validation](../validation/) capability's `Librarian` agent.

The capability is intentionally narrow: it answers "find papers similar to this query" and "fetch the metadata for paper X." It is not a paper-management system; users do not browse the knowledge base directly. They get to it through validation.

## Concepts

- **Paper** (in the knowledge sense) — a published scientific paper with metadata (title, authors, abstract, year, venue, identifiers) and a content embedding. Distinct from a *submitted* paper in [validation](../validation/), which is the user's working artifact.
- **Paper identifier** — a stable id. arXiv id, DOI, Semantic Scholar id. The knowledge capability normalizes across them.
- **Embedding** — a vector representation of the paper's text (currently abstract + title), used for similarity search.
- **Vector search** — given a query string or embedding, return the top-K most similar papers.
- **Full-text search** — given a query string, return papers whose tokenized fields match.
- **Hybrid search** — combination of the two with a relevance reranking step.
- **External lookup** — for papers not in the local index, the capability can fetch metadata from Semantic Scholar via a port.

## Use-cases this capability exposes

(Once migration is complete, each lives as a file under `core/use_cases/knowledge/`.)

- `SearchPapers` — query the index (vector / FT / hybrid), return ranked matches.
- `GetPaper` — fetch a single paper by identifier.
- `LookupExternalPaper` — fetch metadata from Semantic Scholar for a paper not in the local index.
- `IngestPaper` *(admin)* — add or update a paper in the local index. Used by batch jobs that populate the index from arXiv mirror dumps.

## Ports this capability depends on

- [`PaperIndex`](../../ports/decisions/0002-paper-index-port.md) — the local searchable index of papers. Today implemented by LanceDB.
- An **external paper lookup** capability (Semantic Scholar) — currently invoked from inside the `Librarian` service rather than via a named port. A future ADR may extract this as a `PaperLookup` port.

## What this capability is *not*

- Not a recommender. It returns similarity-ranked matches; it does not learn from user behavior to personalize.
- Not the place where papers are *displayed* to users. Validation results reference related papers; the UI for browsing those references is a frontend concern.
- Not a citation graph. It does not track who cites whom across papers. A future capability might.

## Why this is its own capability and not a sub-part of validation

Three reasons:

1. The Librarian is one consumer; future consumers (a "find related work" CLI command, a workspace-scoped "papers I cite" view) will use the same index without going through validation.
2. The index has its own lifecycle: ingestion, embedding refresh, migration between vector stores. Keeping it as a capability gives those concerns a home.
3. The choice of vector store (LanceDB today, pgvector or Qdrant tomorrow) is an adapter swap. Naming the capability separately makes the swap legible.

## ADRs in this capability

| # | Title | Status |
|---|---|---|
| [0001](./decisions/0001-arxiv-as-initial-corpus.md) | arXiv as the initial corpus | accepted |
| [0002](./decisions/0002-knowledge-store-port.md) | `PaperIndex` is a port; today's LanceDB is an adapter | accepted |
| [0003](./decisions/0003-semantic-scholar-via-port.md) | Semantic Scholar lookup becomes its own port | proposed |
