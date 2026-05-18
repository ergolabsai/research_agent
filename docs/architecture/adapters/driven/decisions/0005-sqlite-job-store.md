---
id: adapters-driven-0005
title: SQLite as the `JobStore` adapter for pre-alpha
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The job-store needs to persist pipeline jobs, step logs, and validation results. Choice of relational database for pre-alpha: SQLite (embedded, zero-ops), Postgres (production-grade, requires running a service), or something exotic (DuckDB, RocksDB).

For a team of 3–5 with no production users, SQLite is the right answer: zero ops, zero config, fast for the workload, single file you can copy. Postgres is the right answer *later*.

## Decision

Implement `JobStore` with `SqliteJobStore` using SQLModel + SQLite. Database file lives under `backend/data/`. Schema is materialized via `SQLModel.metadata.create_all()` on startup (see [0009 — No Alembic yet](./0009-no-alembic-yet.md)).

This adapter is explicitly **transitional**: see [0006 — Postgres job store](./0006-postgres-job-store.md) for the planned successor. SQLite serves pre-alpha well; the moment data has business value or concurrent writes appear, the upgrade is queued.

## Consequences

**Easy:**
- `make dev` and `start-dev.bat` create the DB on first run. No setup steps.
- Backups are `cp backend/data/db.sqlite somewhere`.
- The full DB can be inspected with `sqlite3` CLI for debugging.
- Tests use an in-memory SQLite database with no setup.

**Hard:**
- Single-writer semantics. Concurrent pipeline jobs can serialize on writes. Acceptable while the team is small and the user base is small.
- No connection pooling that matters; `check_same_thread=False` is needed and brings its own caveats.
- Schema migrations are absent. Restructure means wipe-and-recreate.

**Forecloses (during pre-alpha):**
- Production-grade concurrency.
- Multi-process job execution against the same store without external coordination.

## Alternatives considered

- **Postgres from day one** — viable but premature. Adds ops surface (running Postgres in dev, in CI, in pre-prod) that does not pay off until the team is larger or the data is valuable.
- **DuckDB** — interesting; OLAP-oriented. Not the workload shape (the job store is OLTP-ish: many small reads and writes).

## Review trigger

- Multi-user concurrent validation becomes a real workload (more than ~1 concurrent paper validation per second).
- A piece of data exists that we are not willing to lose, requiring backups and migrations beyond what `cp` and `create_all` provide.
- The single-writer bottleneck on writes becomes the dominant latency contribution.

When any of these triggers fire, supersede this ADR with [0006](./0006-postgres-job-store.md) (status will move to `accepted`).
