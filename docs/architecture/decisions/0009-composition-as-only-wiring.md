---
id: architecture-0009
title: Composition is the only wiring layer
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

A hexagonal system has pieces that must be connected: use-cases need port implementations, driving adapters need use-cases, configuration must be threaded through. *Somewhere* must know the whole graph.

If that knowledge is scattered — each use-case constructing its own dependencies, each adapter pulling whatever it needs from globals — the boundary the architecture is built to enforce decays into "everyone knows everyone." The architecture turns into a folder rename rather than a structural change.

## Decision

A single `composition/` layer is the **only** place that knows about the whole dependency graph. It:

- Reads configuration (env vars, settings file).
- Constructs each driven adapter with its config.
- Injects driven adapters into use-cases.
- Constructs the driving-adapter entrypoints (FastAPI app, Typer app) and hands them the use-case registry.
- Owns the lifecycle of long-lived resources (connection pools, HTTP clients, background threads).

No other module imports across the boundary. A use-case does not know which `JobStore` implementation it received. A driven adapter does not know which use-case will call it. Only `composition/` knows both.

## Consequences

**Easy:**
- Swapping an adapter is a one-line change in `composition/container.py`.
- Tests construct their own container with fake adapters — the production composition is never imported into a unit test.
- Configuration is read in exactly one place. There is no "where do we look up settings?" question.

**Hard:**
- `composition/` becomes a relatively large module — proportional to the number of ports times the number of supported configurations. This is expected; it is concentrating complexity that would otherwise be diffuse.
- Adding a new port requires a touch to composition. This is a feature, not a bug — it makes the addition visible in code review.

**Forecloses:**
- Module-level singletons in core or adapters. Singletons are hidden composition.
- Use-cases or adapters reading env vars directly. The composition layer reads env vars and passes *values* to constructors.
- Service-locator patterns (`Container.get("job_store")`). Explicit constructor injection only.

## Alternatives considered

- **Each use-case constructs its own dependencies** — rejected. Every use-case becomes a composition root. Configuration logic and adapter selection scatter. Boundary collapses.
- **Global registry / service locator** — rejected. Hides dependencies; an agent reading a use-case cannot tell what it depends on from the signature.
- **Multiple composition modules, one per driving adapter** — viable; deferred. If the API and CLI start needing genuinely different configurations, split `composition/api_app.py` and `composition/cli_app.py` (both already exist as entrypoints) but keep `container.py` shared.

## Review trigger

- `composition/container.py` grows past ~500 lines. At that point a structural refactor inside composition (sub-containers per capability, or a small builder helper) is warranted — but the *concept* (one place knows the graph) does not change.
