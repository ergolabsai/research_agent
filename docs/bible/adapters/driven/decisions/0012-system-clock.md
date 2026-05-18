---
id: adapters-driven-0012
title: System clock with `America/Los_Angeles` timezone
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

`Clock` ([port 0008](../../../ports/decisions/0008-clock-port.md)) needs a production implementation. The decision is trivial — wrap `datetime.now()` — but the *timezone convention* is worth recording so it does not drift.

## Decision

`SystemClock.now()` returns `datetime.now(tz=ZoneInfo("America/Los_Angeles"))`. The project standardizes on this timezone for all timestamps that surface to users (job timestamps, document timestamps, log entries).

UTC is *not* the storage or display convention. The reasoning: the project is operated from the Pacific timezone, and consistency between log files, database rows, and UI display is more valuable than the UTC purist's argument. When (if) the project becomes geo-distributed, the convention may shift.

The timezone constant lives in `core/contracts/time.py` (currently `backend/app/time.py`). The adapter imports the constant.

## Consequences

**Easy:**
- Every timestamp in the system speaks the same timezone. No "is this UTC or Pacific?" debugging.
- The `Clock` port is satisfied by a one-method adapter.

**Hard:**
- DST transitions are real. Timestamps in the spring-forward gap or fall-back overlap can be ambiguous. `ZoneInfo` handles this; just be aware.
- A future geo-distributed deployment will need a convention review.

**Forecloses:**
- Mixed-timezone storage. Pick one; this is the one.

## Alternatives considered

- **UTC for storage, local for display** — viable; the conventional answer. Rejected for the operational reason above: consistency from log file to UI is more valuable for a small team operating from one timezone.

## Review trigger

- The project becomes geo-distributed (multiple teams in different timezones operating the same system).
- A compliance regime requires UTC timestamps in audit logs.
