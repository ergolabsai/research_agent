---
id: architecture-0012
title: No DI framework — plain Python construction in composition
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Python has several dependency-injection frameworks (`dependency-injector`, `wired`, `lagom`, `kink`, `punq`). They offer features like declarative wiring, lifecycle management, scoped containers, lazy resolution, factory registries.

A team that has adopted [composition as the only wiring layer](./0009-composition-as-only-wiring.md) faces a choice: use one of these frameworks to express the wiring declaratively, or hand-construct dependencies in plain Python.

Each path has real costs.

## Decision

**No DI framework.** The composition layer is plain Python: a `container.py` module that constructs adapters and injects them into use-cases via ordinary function calls and constructor arguments.

```python
# composition/container.py
def build_container(settings: Settings) -> Container:
    clock = SystemClock()
    job_store = SqliteJobStore(database_url=settings.database_url)
    llm = AnthropicLLMClient(api_key=settings.anthropic_api_key)
    # ...
    validate_paper = ValidatePaper(job_store=job_store, llm=llm, clock=clock)
    return Container(validate_paper=validate_paper, ...)
```

## Consequences

**Easy:**
- An AI agent reading `container.py` sees the entire dependency graph in one file, in ordinary Python it already knows. No framework-specific conventions, no decorators, no string keys.
- Debugging a "where did this dependency come from?" question is `grep` and a function call chain.
- No new dependency to learn, version-pin, or migrate.
- Tests construct their own miniature container with fake adapters in a few lines.

**Hard:**
- `container.py` grows linearly with the number of adapters and use-cases. Some duplication may appear (two use-cases construct the same `JobStore` instance, for example). Acceptable until the size becomes painful.
- Lazy/scoped instantiation must be implemented by hand if needed. (For 3–5 people, almost never needed.)

**Forecloses:**
- Declarative wiring at module level (e.g., `@inject` decorators that resolve dependencies from a global container).
- "Magic" auto-wiring based on type hints alone.

## Alternatives considered

- **`dependency-injector`** — rejected. Mature and capable, but adds vocabulary (providers, containers, wiring scopes) that must be learned by every contributor. For 3–5 people the cost exceeds the benefit.
- **`lagom`** — rejected for the same reason; lighter but still introduces a framework dependency.
- **Custom auto-wiring by type hint** — rejected. Tempting and small, but creates a runtime resolution layer that obscures the dependency graph.
- **Service locator** — rejected. Hides dependencies; an agent reading a use-case cannot see what it depends on.

## Review trigger

- `container.py` grows past ~500 lines and the duplication starts producing real bugs (mismatched configurations across use-cases that *should* share a dependency).
- A genuine need for scoped containers appears — e.g., per-request lifecycles distinct from process-lifetime singletons — that hand-rolled construction cannot express cleanly.
- A new contributor demonstrates that the hand-construction is genuinely harder to onboard to than a framework would be.
