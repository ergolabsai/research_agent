---
id: architecture-0010
title: Single `pyproject.toml` with `import-linter` for boundaries
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The current `pyproject.toml` installs the entire project as one editable package. This is the simplest layout but lets anything import anything — the very condition the hexagonal architecture is built to prevent. The Python packaging tooling offers several stronger isolation options, each with a different cost.

## Decision

Use a **single `pyproject.toml`** at the repo root, declaring `core`, `adapters`, and `composition` as separate top-level packages via `[tool.setuptools.packages.find]`. Boundary enforcement is delegated to `import-linter` configured in the same `pyproject.toml`, run as a hard CI gate.

This is the *lightest* Python packaging choice that supports the hexagonal layout. Stronger isolation (workspaces, separately-published packages) is available as a future move and is *not* taken now.

## Consequences

**Easy:**
- One `pip install -e .` installs everything. Contributors do not juggle multiple installs.
- One dependency lock, one set of version pins.
- The boundary is enforced *by lint*, which is fast and visible in CI output.

**Hard:**
- The packaging tool does not, by itself, prevent cross-layer imports. Without `import-linter`, this layout is identical to today's. The linter is load-bearing.
- All packages share a single virtualenv. A dependency added for an adapter is technically available to import in core (the lint rule blocks it; the venv does not).

**Forecloses:**
- Independent dependency lifecycles for `core` vs adapters (they are coupled in one lock). Acceptable for now; revisit when adapters genuinely need conflicting versions.

## Alternatives considered

- **`uv` workspaces / PEP 735 dependency groups** (each of `core/`, `adapters/`, `composition/` gets its own `pyproject.toml`, linked as a workspace) — viable. Stronger isolation. Adds friction (multiple installs, multiple lockfiles). Preferred upgrade path if `import-linter` rules start getting bypassed routinely.
- **Separate published packages** — rejected for now. Required only when the project splits into multiple repos.
- **Single flat `pyproject.toml`, no `import-linter`** — rejected. This is the current state and the reason this ADR exists.
- **Monorepo build tool (Bazel, Pants)** — rejected. Out of proportion to current team and project size.

## Review trigger

- Boundary violations land despite `import-linter` (e.g., through dynamic imports the linter cannot see). Move to workspace-style isolation.
- Different parts of the system require incompatible versions of a shared dependency. Move to workspaces or separate packages.
- Adapters develop their own release cadence (separate teams shipping independently). Time to split.
