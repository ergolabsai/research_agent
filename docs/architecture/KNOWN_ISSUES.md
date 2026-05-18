# Known Issues

Short, tracker-style list of bugs and partial implementations. Two rules:

1. Each item is either *getting fixed* (no ADR needed) or *implies a decision* (write an ADR, then link it here and let the issue fall off this list when resolved).
2. This file is not a TODO list. If you wouldn't tell a teammate "this is broken, don't trust it," it doesn't belong here.

## Current

### Security

- **CORS is fully open** (`allow_origins=["*"]`). Acceptable in pre-alpha, blocking for production. Implies an ADR: how CORS is configured per environment.
- **`/users/search` has no auth requirement**. Anyone can list users. Should be fixed in the same pass that introduces `Principal`-flow authz (see [0005-principal-in-every-usecase](./decisions/0005-principal-in-every-usecase.md)).

### Persistence

- **No Alembic migrations.** Schema is materialized by `SQLModel.metadata.create_all()`. Acceptable while we still freely wipe the DB; blocks the moment data has value. See [adapters/driven/0009-no-alembic-yet](./adapters/driven/decisions/0009-no-alembic-yet.md).
- **`figures_json` stores base64-inlined image data on the job row.** Row size balloons; query plans degrade. Implies an ADR on figure storage (large blobs belong in object storage, not the relational store).

### Dead dependencies

- `frontend/package.json` carries `draft-js`, `react-draft-wysiwyg`, `zustand`, none currently imported. Remove on next dep cleanup pass — not a decision, just hygiene.
- `backend/requirements.txt` carries `instructor`; structured output uses `with_structured_output()` instead. Same — remove on cleanup.

### Pipeline shape

- **Structured validation output.** `compile_results` returns `ValidationResult` with `overall_assessment.review` as a single markdown blob; the frontend parses it for display. The contract should be structured JSON. Implies an ADR on the validation-result contract shape. Frontend `GraphAnalysis` type already documents the target shape.

## Cleared (kept for history)

_(empty for now; items move here with a one-line note when resolved, then get deleted after a release or two.)_
