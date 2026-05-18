---
id: adapters-driven-0009
title: No Alembic migrations yet — schema via `create_all`
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Schema migrations are essential when data has business value and the schema evolves over time. They are *premature* when data is freely wipable, the team is small, and the schema is still in flux.

The project is in the latter state. Today, schema is materialized by `SQLModel.metadata.create_all()` on startup. This is not a defect — it is the right answer for the stage.

The risk is that "we'll add migrations later" becomes "we never added migrations" and the project enters production with no migration path.

## Decision

**Continue using `SQLModel.metadata.create_all()` for now.** Do not introduce Alembic.

Trigger to introduce Alembic: the moment the SQLite job store is superseded by Postgres ([0006](./0006-postgres-job-store.md)). At that point migrations become non-negotiable, and Alembic is the standard SQLModel/SQLAlchemy companion.

This is a deliberate "we know we are skipping a step" decision, not an oversight.

## Consequences

**Easy:**
- Schema changes are: edit the model, restart the app, wipe the DB if needed. Zero ceremony.
- New contributors do not learn Alembic before they can run the app.

**Hard:**
- Any data in the SQLite store is sacrificial. This is currently fine.
- Production deployment cannot use `create_all` — it would silently fail to add new columns to existing tables. Alembic is a hard requirement before production.

**Forecloses:**
- Carrying pre-alpha data forward into production through migrations. The cutover to Postgres + Alembic involves a one-shot ETL, not a migration chain from day one.

## Review trigger

- The Postgres job store transition (Step 3 of migration). Alembic is introduced as part of that change; this ADR is superseded.
- Any specific dataset emerges that we are not willing to lose (e.g., a real user's workspace). At that point Alembic is introduced regardless of the Postgres transition timeline.
