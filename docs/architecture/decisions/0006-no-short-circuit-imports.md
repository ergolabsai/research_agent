---
id: architecture-0006
title: No short-circuit imports across layers
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The hexagonal boundary depends on each layer only knowing about its neighbors:

- Driving adapters know about use-cases (and contracts).
- Use-cases know about ports, domain, services, contracts.
- Driven adapters know about ports and external infrastructure.
- Composition knows everything — but is the *only* place that does.

The temptation to short-circuit is constant: "the CLI needs to look up a job — surely importing the job-store adapter directly is easier than going through a use-case." Each such shortcut chips at the boundary. Six months in, the CLI knows about Postgres, the LLM client, and MinIO directly, and the hexagon is dead.

## Decision

The following imports are **forbidden** and enforced by `import-linter`:

1. `core/*` may not import from `adapters/*` or `composition/*`.
2. `adapters/driving/*` may not import from `adapters/driven/*`. (A driving adapter that needs data goes through a use-case.)
3. `adapters/driven/*` may not import from `adapters/driving/*` or from other driven adapters. (Each driven adapter is self-contained.)
4. `adapters/*` may not import from `composition/*`.
5. Only `composition/*` may import from both `core/*` and `adapters/*`.

The rule applies recursively: an indirect import path that reaches a forbidden module also violates the rule.

## Consequences

**Easy:**
- A new contributor — human or AI — can determine the layer of any file by where it imports *from*, not by where it lives.
- Layer violations cannot land. CI is the gate.
- Refactors that "move things around" are immediately validated: if `import-linter` passes after the move, the layering is intact.

**Hard:**
- The CLI cannot make a "quick" direct call to a job-store adapter. It must call a `GetJob` use-case. The use-case may be one line. That is fine.
- Cross-adapter coordination (e.g., a driven adapter that needs to call another driven adapter) goes through composition or — more honestly — gets refactored. If two driven adapters need each other, one of them is probably a service that belongs in core.

**Forecloses:**
- "Helper" modules that bridge adapters informally.
- Driving adapters constructing their own driven-adapter instances.
- Driven adapters subscribing to events fired by driving adapters.

## Alternatives considered

- **Convention only, no CI gate** — rejected. The current project history shows that conventions without enforcement decay. See the import surface of `backend/app/services/pipeline_service.py` today.
- **Allow `adapters/driven/*` to share via a `common` module** — rejected as a default; deferred until concrete duplication appears. Premature sharing creates coupling that is harder to undo than the duplication it avoids.
- **Pre-commit hook instead of CI** — rejected as primary gate. Pre-commit hooks can be skipped (`--no-verify`); CI cannot. The hook is welcome as an early warning.

## Review trigger

- Repeated cases where the rule causes a use-case to be created that does nothing except wrap a single port call. If this is *only* what the use-case does, that is fine (see [0005](./0005-principal-in-every-usecase.md) corollary). If many use-cases collapse into trivial pass-throughs and the cost outweighs the audit benefit, revisit.
- A legitimately cross-cutting concern (telemetry, tracing) requires adapters to share a transport — at which case introduce a `common/` module with strict scope, not a free-for-all.
