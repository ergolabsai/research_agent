# Migration: current code → hexagonal architecture

This is a **time-bound** document. It points into the current codebase with file-and-line precision so the migration work can be planned and executed. Line numbers will drift inside any single commit; do not rely on them after the migration begins. Archive (or delete) this file when migration is complete — the ADRs are the timeless record.

## Status

**Not started.** The bible is in place; no code has been moved yet. The user has indicated the codebase was written in a few days and can be rewritten or scrapped — the migration is therefore *one of three options*:

1. **Strangler-fig migration** — move files and dependencies incrementally, preserve behavior.
2. **Greenfield rewrite** — start a new layout, copy logic over file by file from the old code.
3. **Hybrid** — extract contracts and ports first as fresh code, then port use-cases and adapters from the old code.

The decision between these is open. This document describes option 1 by default because it is the most concrete; option 3 is plausibly faster and option 2 is plausibly cleaner. See "Migration mode" below.

## Migration mode

Three plausible modes, listed in increasing levels of "throw it out":

### Mode A: Strangler-fig (incremental)

Move existing files into the new layout, breaking and re-wiring dependencies as you go. Old and new code coexist for a window; `make dev` must work at every commit.

Pro: never breaks the prototype. Predictable.
Con: more total work; carries existing code shape forward.

### Mode B: Greenfield rewrite

Create `core/`, `adapters/`, `composition/` empty. Write the use-cases, ports, and adapters fresh, copying logic from the old code file-by-file but not the file structure. Old code is deleted at the end.

Pro: cleaner result. The architecture is built into the code from line 1.
Con: a larger gap during which the old code is running and the new code is incomplete. Easy to lose subtle behaviors that were not noticed in the old code.

### Mode C: Hybrid

Extract `core/contracts/` and `core/ports/` first as fresh code (small, declarative, no logic). Then port each use-case and adapter from the old code into the new layout — but with the freedom to rewrite where the old shape doesn't fit.

Pro: balances cleanness and safety. The contracts and ports are correct from day one; the implementation is migration.
Con: requires the contracts to be reasonably right before any use-case is written.

**Recommendation:** Mode C. The contracts and ports are the load-bearing pieces; getting them right first is more valuable than preserving any specific implementation shape.

If Mode B is chosen, this MIGRATION.md becomes mostly irrelevant — the pointers below are for *what to copy from*, not *what to refactor in place*.

---

## Pointers into the current code

These are the seams that matter, as of the time of writing. Lines are accurate as of the commit at which this file was written; expect drift within hours of starting any change.

### The big seam: API → pipeline

The single biggest coupling point in the current code:

- `backend/app/services/pipeline_service.py:26-40` — imports `AdvisorOrchestrator` plus 10 graph helpers and the `ValidationResult` schema directly from `advisor_pipeline`. This entire import block becomes a use-case (`ValidatePaper`) that calls the orchestrator (a core service) through composition.

### Module-level singletons (become injected dependencies)

These are the hidden globals that breach [architecture/0009 — Composition is the only wiring layer](./decisions/0009-composition-as-only-wiring.md). Every one must become a constructor parameter:

- `advisor_pipeline/llm.py:46-52` — `_llm = _build_llm()` at module scope; `get_llm()` returns the global. Becomes `LLMClient` port + `AnthropicLLMClient` adapter, injected into agents.
- `advisor_pipeline/utils/lancedb_search.py:43-57` — `_db_connection` and `_table` globals. Become `PaperIndex` port + `LanceDBPaperIndex` adapter.
- `advisor_pipeline/mcp_client.py:22-50` — `CalculatorClient` with its background asyncio loop. Becomes `Calculator` port + `McpCalculatorClient` adapter; the threading bridge moves to the adapter.
- `backend/app/services/pipeline_service.py:54-55` — `_graphs: dict[str, nx.DiGraph]` in-memory cache. Becomes a small `GraphCache` port (or folds into Redis later); for now, an adapter that wraps an LRU dict.

### Backend → pipeline config imports

These imports cross what should become a layer boundary:

- `backend/app/security.py:10` — `from advisor_pipeline.config.settings import settings`. The shared settings object is fine in principle but the *location* of the settings module needs to move to `composition/settings.py` once the layout is in place. Both halves of the system read from there.
- `backend/app/storage.py:5` — same import. Same resolution.

### Files that move wholesale (with the renaming pattern)

Mode A and Mode C only. Mode B copies content, not files.

| Current location | New location | Notes |
|---|---|---|
| `advisor_pipeline/models/schemas.py` | `core/contracts/validation.py`, `core/contracts/paper.py`, `core/contracts/jobs.py` | Split by aggregate. The current single-file shape is fine to copy then split. |
| `advisor_pipeline/orchestrator.py` | `core/services/orchestrator.py` | LangGraph coordination is allowed in core ([capabilities/validation/0002](../capabilities/validation/decisions/0002-langgraph-in-core.md)). Per-node I/O moves to port calls. |
| `advisor_pipeline/agents/figure_evaluator.py` (or wherever it lives today) | `core/services/figure_evaluator.py` | Constructor takes `LLMClient`. |
| `advisor_pipeline/agents/math_evaluator.py` | `core/services/math_evaluator.py` | Constructor takes `LLMClient` and `Calculator`. |
| `advisor_pipeline/agents/librarian.py` | `core/services/librarian.py` | Constructor takes `LLMClient` and `PaperIndex` (+ eventually `PaperLookup`). |
| `advisor_pipeline/models/paper_graph.py` | `core/domain/graph.py` | NetworkX wrapper, pure Python. |
| `advisor_pipeline/llm.py` (post-singleton) | `adapters/driven/llm/anthropic.py` | The build function and retry decorator move; the global goes away. |
| `advisor_pipeline/mcp_client.py` | `adapters/driven/mcp/calculator_client.py` | Threading bridge stays here, encapsulated. |
| `advisor_pipeline/utils/lancedb_search.py` | `adapters/driven/paper_index/lancedb.py` | The helpers become methods on the adapter; the globals go away. |
| `backend/app/services/pipeline_service.py` | Split: most into `core/use_cases/validation/` and `core/services/`; SQL parts into `adapters/driven/job_store/sqlite.py`; figure-hydration into `adapters/driven/object_storage/local.py` (or a dedicated `FigureHydrator` adapter). | This is the file that fragments most across the new layout. |
| `backend/app/routes/*.py` | `adapters/driving/api/routes/*.py` | Each route slims to parse → use-case → format. Pydantic request/response models stay; they import from `core/contracts/`. |
| `backend/app/security.py` | Split: JWT logic → `adapters/driven/identity/jose_token_issuer.py`; bcrypt → `adapters/driven/identity/bcrypt_password_hasher.py`; `Principal` construction middleware → `adapters/driving/api/auth.py`. | The current `security.py` is a junk drawer; it explodes into three files. |
| `backend/app/storage.py` | `adapters/driven/object_storage/local.py` and `adapters/driven/object_storage/minio.py` | The current branching becomes polymorphism. |
| `backend/app/models.py` | Stay in adapter land as the SQLModel schema. Mirror the entities as plain Pydantic in `core/contracts/` (User, Document, Workspace, etc.). | The SQLModel models are infrastructure (they know about tables); the contract types are core. |
| `scripts/start-dev.bat` | `deploy/scripts/start-dev.bat` | Pure relocation. |
| `docker/docker-compose.yml`, `docker/python.Dockerfile` | Split into per-service Dockerfiles under `deploy/docker/` per [infrastructure/0002](../infrastructure/decisions/0002-docker-compose-topology.md). | |

### Where Principal construction lives

- The `Principal` value object: new file at `core/contracts/auth.py` (or `core/authz.py`). Carries identity, roles, source.
- API-side construction: in `adapters/driving/api/auth.py` as FastAPI middleware. Reads JWT, calls `TokenIssuer.verify_access_token`, builds `Principal`, attaches to request scope.
- CLI-side construction: in `adapters/driving/cli/auth.py`. Reads local token from config file, calls same `TokenIssuer`, builds `Principal`.
- System / internal: in `composition/` when constructing background jobs — `Principal(role="system", ...)`.

### Frontend touchpoints

- `frontend/src/types/index.ts:139` — hand-mirrored `ValidationResult` interface. Becomes generated ([frontend/0004](../frontend/decisions/0004-generated-types-from-contracts.md)). The generator script lives under `scripts/codegen/` and emits `frontend/src/types/generated.ts`.
- `frontend/src/api/client.ts` — axios setup. Stays roughly as-is; its modules (`authAPI`, `documentsAPI`, etc.) become thin wrappers around the generated types.

### `pyproject.toml`

- Current `pyproject.toml:69-71` declares one editable package. Becomes:
  - Multiple package declarations under `[tool.setuptools.packages.find]` for `core`, `adapters`, `composition`.
  - A `[tool.importlinter]` section with the boundary contracts from [process/0001](../process/decisions/0001-import-linter-as-ci-gate.md).
  - The script entry point `advisor = composition.cli_app:main` for the CLI.

---

## Suggested migration order

Independent of mode (A/B/C). Each step ends with a working `make dev`.

1. **Contracts and ports first.** Write `core/contracts/` (the data shapes) and `core/ports/` (the Protocol declarations) as fresh code. No use-cases yet. Add `import-linter` with rules limited to the new code initially.
2. **One use-case as proof of concept.** `ValidatePaper`. Wire it through `composition/container.py` with adapters that wrap the current code (e.g., `LegacyPipelineServiceJobStore` that delegates to the old `pipeline_service.py`). The FastAPI route changes to call the use-case.
3. **Migrate the orchestrator and agents to core services.** Each agent class gets a constructor with injected ports. The current globals (`get_llm()`, `CalculatorClient()`) go away.
4. **Migrate driven adapters.** LLM, paper index, calculator, job store, object storage. Each becomes a single-file adapter satisfying a port.
5. **Migrate the rest of the use-cases.** Document, workspace, identity, knowledge.
6. **Tighten `import-linter` rules to cover the whole project.** At this point all code is in the new layout.
7. **Add the CLI driving adapter.** First-class per [architecture/0007](./decisions/0007-cli-first-driving-adapter.md).
8. **Step 3-5 of the original plan** (Postgres, auth, pipeline-as-service) become follow-ups, each with its own ADRs.

## Verification per step

Each step's done-criterion:

- `make dev` runs both backend and frontend without errors.
- Existing manual smoke-tests pass (login, submit paper, see results).
- `import-linter` is green for the layout that exists so far.
- No regression in the figure / math / librarian step outputs (compare a fixture-driven validation before and after).

## When to archive this document

When all the file moves listed here are complete and the `import-linter` contracts cover the whole project, this file is no longer current — it describes a path no longer being walked. At that point: move to `docs/bible/_archive/MIGRATION-2026.md` or similar, with a header noting the date the migration completed.
