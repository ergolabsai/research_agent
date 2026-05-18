---
id: ports-0004
title: `JobStore` port for pipeline job persistence
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The validation pipeline produces long-running jobs: a paper is submitted, the orchestrator runs eight steps, and at each step intermediate state must be persisted (for progress tracking, transparency, and crash recovery). Today this state lives in SQLite via SQLModel, with the persistence code mixed into the FastAPI service layer.

The use-cases that *consume* this state — get a job, list jobs, fetch step logs — need a clean interface. The choice of *storage* (SQLite now, Postgres later) is implementation, not architecture.

## Decision

```python
class JobStore(Protocol):
    async def create(self, job: Job) -> None: ...

    async def get(self, job_id: JobId) -> Job | None: ...

    async def list_for(
        self,
        principal: Principal,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> JobPage: ...

    async def update_status(
        self,
        job_id: JobId,
        status: JobStatus,
        *,
        error: str | None = None,
    ) -> None: ...

    async def update_progress(
        self,
        job_id: JobId,
        current_step: int,
        step_name: str,
    ) -> None: ...

    async def save_step_log(self, log: StepLog) -> None: ...

    async def list_step_logs(self, job_id: JobId) -> list[StepLog]: ...

    async def get_step_log(self, job_id: JobId, step_name: str) -> StepLog | None: ...

    async def save_result(
        self,
        job_id: JobId,
        result: ValidationResult,
        graph_json: str,
    ) -> None: ...
```

`Job`, `JobStatus`, `JobPage`, `StepLog`, `JobId` are contract types in `core/contracts/jobs.py`.

The port carries authorization context (`list_for(principal, ...)`) where listing semantics require it — listing is filtered by principal at the port level. Single-job operations do *not* take a Principal; the use-case checks ownership after fetching.

## Consequences

**Easy:**
- The use-cases for jobs (validate, list, get, get-step-logs) call port methods. No SQLModel imports outside the adapter.
- SQLite → Postgres is an adapter swap.
- The orchestrator's step-completion callback calls `save_step_log(...)` — a port method — instead of importing the SQLModel `PipelineStepLog`.

**Hard:**
- The port surface is wider than other ports because the orchestrator interacts with it at every step (status, progress, step log, final result). Each method must remain stable as adapters change; reshaping the port is a cross-adapter change.
- Pagination (`cursor: str | None`) is a soft contract — the adapter chooses the encoding. Document this in the adapter ADR.

**Forecloses:**
- Use-cases that pull SQL directly. Even queries that "feel SQL-shaped" (sort, filter, paginate) go through port methods.

## Adapters

- **`SqliteJobStore`** — current. SQLModel + SQLite. Default for pre-alpha.
- **`PostgresJobStore`** — proposed (Step 3 of migration). SQLModel + Postgres via psycopg.
- **`InMemoryJobStore`** — test fake. Dict-backed.

See [adapters/driven/decisions/0005-sqlite-job-store.md](../../adapters/driven/decisions/0005-sqlite-job-store.md) and [0006-postgres-job-store.md](../../adapters/driven/decisions/0006-postgres-job-store.md).

## Review trigger

- A use-case needs a query the port cannot express (e.g., "jobs grouped by hour of submission for the dashboard"). Add a port method named for the use, not for the SQL shape.
- Performance: if the port becomes a hot loop for status updates, batch the writes inside the adapter.
- The in-memory `_graphs` cache today (the live NetworkX graph for a job) is a separate concern from `JobStore`. Worth its own port (`GraphCache`) if it grows past trivial use.
