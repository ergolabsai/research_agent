---
id: process-0001
title: `import-linter` as a hard CI gate for hexagonal boundaries
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Hexagonal architecture survives only as long as the boundary rules are enforced. [0003 — Core has no I/O](../../decisions/0003-core-has-no-io.md) and [0006 — No short-circuit imports](../../decisions/0006-no-short-circuit-imports.md) describe the rules. The question is *how* they get enforced.

Three options:

1. **Code review only** — eventually decays as reviewers tire.
2. **Pre-commit hooks** — can be skipped with `--no-verify`; not a real gate.
3. **CI gate** — cannot be skipped without a deliberate merge override visible to all.

## Decision

Use **`import-linter`** as the boundary enforcement tool, configured in `pyproject.toml`, run as a **mandatory CI step** that blocks merges on failure.

The contracts include:

- `core/*` cannot import any module under the I/O allow-deny list (`fastapi`, `sqlite3`, `httpx`, `anthropic`, `langchain` modules that perform I/O, `lancedb`, `mcp`, `boto3`, `minio`, etc.). Exception: LangGraph coordination primitives are explicitly allowed per [capabilities/validation/0002](../../capabilities/validation/decisions/0002-langgraph-in-core.md).
- `core/*` cannot import from `adapters/*` or `composition/*`.
- `adapters/driving/*` cannot import from `adapters/driven/*`.
- `adapters/driven/*` cannot import from `adapters/driving/*` or from other `adapters/driven/*` modules.
- `adapters/*` cannot import from `composition/*`.

The contracts file (or the `pyproject.toml` section) lives next to the code. Adding a new boundary rule is a PR; loosening one requires explicit approval and an ADR if it changes the architecture.

A pre-commit hook is welcome as an *early* signal (developers see the failure before pushing), but the CI gate is the authoritative one.

## Consequences

**Easy:**
- Boundary violations cannot land. New contributors (human or AI) see the rule fire immediately.
- Refactors that move code around can verify they did not break layering by running one command.
- The rule set is version-controlled and reviewable — changes to the rules are deliberate.

**Hard:**
- False positives waste time. The rule set must be tuned; an allow-list of known-safe imports is part of the configuration.
- `import-linter` cannot see dynamic imports (`importlib`, `__import__`). The architecture relies on contributors not using dynamic imports to evade the rules.

**Forecloses:**
- "Just this once" boundary breaches as a routine practice.

## Alternatives considered

- **No CI gate, code review only** — rejected. See the original `pipeline_service.py` import surface for evidence of decay without enforcement.
- **Custom AST script** — rejected. `import-linter` does this job; reimplementing it badly is wasted work.
- **`deptry` or `pip-deptry` for unused-dep checking** — complementary, not a substitute. `import-linter` checks *boundaries*; `deptry` checks *dependencies*. Both are useful; this ADR is about boundaries.

## Review trigger

- The rule generates more than ~1 false positive per month on legitimate code. Audit the allow-lists.
- A class of architectural violation slips through that `import-linter` cannot catch (dynamic imports, runtime registration). Reach for a different tool or AST-based linting in addition.
