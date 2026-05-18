---
id: adapters-driven-0013
title: SQLite + SQLModel as the repository adapters for collaboration and identity
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The repository ports ([port 0009](../../../ports/decisions/0009-repository-ports.md)) — `UserRepository`, `WorkspaceRepository`, `DocumentRepository`, `AttachmentRepository` — need implementations. The collaboration and identity capabilities depend on them.

The choice mirrors [the SQLite job store](./0005-sqlite-job-store.md): SQLite is right for pre-alpha, Postgres is the planned successor. Same SQLModel models, same engine swap pattern.

## Decision

Implement the four repository ports with SQLite + SQLModel adapters:

- `SqliteUserRepository`
- `SqliteWorkspaceRepository`
- `SqliteDocumentRepository`
- `SqliteAttachmentRepository`

All share the same engine (`engine = create_engine(settings.database_url, ...)`) — currently the same SQLite file as the job store. The shared engine is intentional: the four entities + jobs are all in one logical store. Splitting stores would create coordination needs (cross-store transactions) that nothing benefits from at this stage.

Each repository takes an `engine` in its constructor and opens a `Session` per call. Sessions are short-lived; no long-running transactions.

Implementation note: the current code has these as SQLModel models manipulated directly from FastAPI route layer (`backend/app/routes/*.py`). The migration wraps the SQLModel access in repositories that satisfy the ports.

## Consequences

**Easy:**
- Same engine, same patterns, same migration story as the job store.
- A test fake (`InMemoryUserRepository` etc.) is straightforward — dict-backed.
- The composition layer constructs all four repositories with one shared engine.

**Hard:**
- Cross-aggregate atomicity (e.g., "create document and add attachment in one transaction") is not part of the port surface. The current SQLite engine allows it via a shared session, but the port shape does not express it. If atomicity becomes needed, introduce a `UnitOfWork` port — but most use-cases do not need it.
- The shared engine is a hidden coupling between job store and repositories. If they ever migrate to different stores at different times, the composition layer must support multiple engines simultaneously. Plan for this in [0006](./0006-postgres-job-store.md)'s rollout.

**Forecloses:**
- Per-aggregate stores (e.g., users in one DB, documents in another). Not desirable now; the cost would exceed the benefit.

## Alternatives considered

- **Direct SQLModel use without repository ports** — rejected. This is the current state. Use-cases would import SQLModel; the boundary breaks.
- **A single `Database` god-repository** — rejected per [ports/0009](../../../ports/decisions/0009-repository-ports.md).
- **An ORM other than SQLModel** (raw SQLAlchemy, Tortoise, Pony) — rejected. SQLModel is already in the codebase, Pydantic-compatible (matches the contract layer), and adequate.

## Review trigger

- The Postgres transition. The repositories become `PostgresUserRepository` etc. (likely with minimal code change since SQLModel is engine-agnostic). New ADRs supersede these.
- A repository becomes a hot spot for queries the port shape cannot express. Add port methods; resist leaking SQL.
