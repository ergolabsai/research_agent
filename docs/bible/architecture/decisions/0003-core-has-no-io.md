---
id: architecture-0003
title: Core has no I/O
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

[Hexagonal architecture](./0002-adopt-hexagonal-architecture.md) requires the core to know nothing about the outside world. "Knows nothing about the outside world" is a vague phrase that decays quickly under pressure ("just one HTTP call, just for this one use-case"). It must be made into a rule that is enforceable, not a guideline that is aspirational.

## Decision

The `core/` layer performs **no I/O of any kind**. Not minimal I/O — none.

**Forbidden imports inside `core/`:** any package that performs network I/O (`httpx`, `requests`, `aiohttp`, `urllib`), database access (`sqlite3`, `sqlmodel`, `sqlalchemy`, `psycopg`), filesystem operations beyond `pathlib` value objects, web frameworks (`fastapi`, `starlette`, `flask`), CLI frameworks (`click`, `typer`), LLM SDKs (`anthropic`, `openai`), orchestration libraries that perform I/O (`langchain`'s I/O-touching modules), vector stores (`lancedb`, `qdrant-client`), protocol clients (`mcp`), object storage clients (`boto3`, `minio`).

**Allowed imports inside `core/`:** Python stdlib (excluding I/O modules — no `socket`, no `urllib`, no `sqlite3`), `pydantic`, `pydantic-settings` *for contract definitions only*, `networkx`, `sympy`, `typing`, `typing_extensions`, `dataclasses`. *Coordination* libraries (e.g., `langgraph` for the validation orchestrator) are allowed *only* if they do not themselves perform I/O.

Enforcement is a hard CI gate via `import-linter`, not a code-review convention. See [process/0001-import-linter-as-ci-gate](../../process/decisions/0001-import-linter-as-ci-gate.md).

## Consequences

**Easy:**
- Unit-testing the core is genuinely fast: no test database, no network mocks, no monkey-patching of SDK clients. Tests use fake adapters and run in milliseconds.
- Reasoning about a use-case is local: every external dependency is declared on its constructor.
- Swapping infrastructure is a composition-layer change. Always.

**Hard:**
- The first time a use-case "obviously" needs to make an HTTP call to an external API, the answer is "no — define a driven port for it." This will feel like overkill until the second adapter (e.g., the CLI) tries to reuse the same use-case.
- LangGraph in core requires a careful boundary: the *graph structure* and *node sequencing* are pure; the *work each node does* must go through ports. See [capabilities/validation/0002-langgraph-in-core](../../capabilities/validation/decisions/0002-langgraph-in-core.md).
- pydantic-settings can read environment variables, which is technically I/O. By convention, settings are constructed in the composition layer and passed *as values* into the core — the core never imports `pydantic_settings` to read env directly.

**Forecloses:**
- "Just import requests in this one helper." Even one breach normalizes the next. The lint rule is the rule.
- Storing module-level singletons in core (`_llm = build_llm()`). These are hidden I/O at import time.

## Alternatives considered

- **"Mostly no I/O" with case-by-case exceptions** — rejected. Exceptions accumulate. The boundary erodes within months.
- **Allow I/O but isolate it to a `core/infrastructure/` submodule** — rejected. This is just a layered architecture wearing a hexagonal hat; the dependency direction inverts the boundary's intent.
- **Static analysis without CI enforcement** — rejected. A warning that does not block a merge is a warning that gets ignored.

## Review trigger

- The lint rule generates more than ~1 false positive per month on legitimate code. At that point the allow-list is wrong, not the rule.
- A new pure-Python library appears that would clearly belong in core but is incorrectly classified as I/O (e.g., a new graph algorithm package). Update the allow-list explicitly; do not weaken the principle.
