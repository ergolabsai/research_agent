---
id: adapters-driven-0006
title: Postgres as the `JobStore` adapter for production
status: proposed
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The SQLite job store ([0005](./0005-sqlite-job-store.md)) is explicitly transitional. The migration plan calls for Postgres as Step 3 of the architectural rollout. This ADR documents the proposal so the choice is settled before code is written.

## Decision (proposed)

Implement `JobStore` with `PostgresJobStore` using SQLModel + Postgres via psycopg (the dominant modern Postgres driver). Same SQLModel models; the engine differs.

A managed Postgres is preferred (Supabase, Neon, or a similar service) over self-hosted, for pre-production scale. The dedicated server may eventually host its own Postgres if cost or compliance demands.

Alembic migrations are introduced as part of this transition (see [0009](./0009-no-alembic-yet.md)'s eventual supersession).

## Consequences (anticipated)

**Easy:**
- Concurrent writes are no longer a bottleneck.
- Connection pooling, robust transactions, mature backups, point-in-time recovery.
- Same SQLModel code — the engine swap is largely transparent to model definitions.

**Hard:**
- A real database service must be available in dev, CI, and pre-prod. Either a managed service per environment or a Docker Compose Postgres in dev.
- Schema migrations are no longer optional: Alembic enters the build.
- Tests against real Postgres are slower than in-memory SQLite. Use SQLite for unit tests of the *repositories* themselves; use Postgres-in-CI for integration tests.

**Forecloses:**
- Single-file portability. The `cp db.sqlite` backup is gone; backup is now a Postgres concern.
- Zero-config dev. Postgres in dev is one more thing to run.

## Alternatives considered

- **MySQL / MariaDB** — viable; less common in the Python ecosystem for new projects. Postgres has better JSON support (relevant for `result_json`, `graph_json` columns).
- **Stay on SQLite indefinitely** — rejected. The concurrent-write ceiling is real; pre-production data deserves backups and migrations.

## Migration plan (high level)

1. Stand up Postgres in dev (Docker Compose service or managed-service Dev Plan).
2. Add Alembic to the project; generate the initial migration from current SQLModel models.
3. Implement `PostgresJobStore` (likely 90% identical to `SqliteJobStore` — both go through SQLModel).
4. Switch composition to construct `PostgresJobStore` when `DATABASE_URL` points to Postgres.
5. One-shot ETL of existing pre-alpha SQLite data into Postgres (a script, not a migration).
6. Run both adapters in parallel for one release; cut over.
7. Supersede [0005](./0005-sqlite-job-store.md): mark it `superseded`, set `superseded-by: ["adapters-driven-0006"]`.

## Review trigger

- This ADR is `accepted` (status flips during Step 3).
- During the transition: any data loss or downtime caused by the cutover indicates the plan needs revision.
