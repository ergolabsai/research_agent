---
id: frontend-0004
title: Frontend TypeScript types generated from backend Pydantic contracts
status: proposed
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The frontend uses TypeScript interfaces for API responses (`ValidationResult`, `GraphAnalysis`, etc.) that are *hand-mirrored* from the backend's Pydantic models. This is a constant drift source: the backend changes a field, the frontend silently breaks at runtime when the new shape arrives.

The hand-mirroring is also error-prone: small typos in optional fields, mismatched casing, fields missing entirely.

Once the core's contracts ([0002 — Adopt hexagonal architecture](../../decisions/0002-adopt-hexagonal-architecture.md)) become authoritative, the frontend types should be *generated* from them, not hand-mirrored.

## Decision (proposed)

Generate `frontend/src/types/generated.ts` from the backend's Pydantic contracts at the boundary between core and the API adapter. Two implementation paths:

1. **OpenAPI codegen** — the FastAPI server exposes OpenAPI; `openapi-typescript` or similar generates a `types.ts` from the spec. The build script runs the generator against the running API in CI.
2. **Direct Pydantic → TypeScript** — a tool like `pydantic2ts` reads the Pydantic models and emits TypeScript directly, no API runtime needed.

Path 2 (`pydantic2ts`) is preferred because:

- Codegen does not require running the API.
- Pydantic models in `core/contracts/` are the *authoritative* source — they exist whether the API is running or not.
- The CLI adapter (also a consumer of these types, via `--json`) benefits from the same generated types when it gets a TypeScript wrapper. (Today the CLI is Python, so the analogy is via Pydantic itself; but a TS CLI port is conceivable.)

The generated file is committed to git (so the frontend builds without a Python step). Generation is a pre-build step that diffs the result; CI fails if the committed file is out of date.

## Consequences (anticipated)

**Easy:**
- The frontend's types match the backend's contracts by construction.
- API shape changes are immediately visible in the frontend as TypeScript errors during build.
- The hand-mirrored types in `src/types/index.ts` shrink to just the *frontend-only* additions (UI-state types, derived view models) — server-shape types come from `generated.ts`.

**Hard:**
- One more codegen step in the build. Acceptable if it is fast and the failure mode is clear.
- Backend devs must run the generator after contract changes (or accept CI failures and re-run). A pre-commit hook helps.
- Some Pydantic types do not translate cleanly to TypeScript (e.g., discriminated unions need careful tagging). The contracts may need lightweight adjustments to round-trip cleanly.

**Forecloses:**
- Continued hand-mirroring. Once generated, drift is not tolerated.

## Alternatives considered

- **OpenAPI codegen (path 1)** — viable; widely used. Rejected as default because it requires the API runtime and adds a dependency on FastAPI's OpenAPI generation accuracy.
- **No generation; manual sync with stronger discipline** — rejected. The current state. Drift continues.
- **Shared schema language (e.g., Protobuf)** — overkill. Pydantic + a generator is much simpler at this scale.

## Status: proposed, not yet accepted

Acceptance happens when:

1. The core's contracts are extracted ([architecture migration Step 1](../../MIGRATION.md)).
2. `pydantic2ts` (or equivalent) is added to the dev dependencies with a documented generator script.
3. `frontend/src/types/index.ts` is reduced to frontend-only additions plus a `generated.ts` import.

## Review trigger

- This ADR is accepted (status flips to `accepted`).
- The generator tool becomes unmaintained or chokes on a Pydantic feature the contracts need. Switch to OpenAPI codegen (path 1) at that point.
