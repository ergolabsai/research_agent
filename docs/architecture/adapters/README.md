# Adapters

Adapters connect the [core](../) to the outside world. They come in two flavors with different responsibilities:

- **Driving adapters** ([driving/](./driving/)) translate input from a user or external system into a use-case call. CLI, HTTP API, React frontend.
- **Driven adapters** ([driven/](./driven/)) implement [driven ports](../ports/) — they are how the core *reaches out* to infrastructure. LLM clients, paper indices, job stores, object storage, token issuers.

This README is the entry point. Each subfolder has its own README and an ADR catalog.

## What an adapter is allowed to do

A driving adapter:

- Parses input (HTTP request body, CLI flags, frontend props).
- Constructs a `Principal` from the adapter's credential mechanism (JWT for HTTP, local token for CLI).
- Calls one use-case (occasionally two for trivial composition like "look up an id before passing it to another use-case").
- Formats output (HTTP JSON response, CLI text or `--json`, frontend props).

A driven adapter:

- Implements a driven port (a `Protocol` declared in [core/ports/](../ports/)).
- Translates port method calls into infrastructure calls (DB queries, HTTP calls, SDK calls).
- Handles infrastructure concerns: retries, connection pooling, rate limiting, error translation.

## What an adapter is *not* allowed to do

- **Business logic** — does not belong in an adapter. If a CLI command needs "validate a paper and then list related papers," the right answer is a use-case that does both, not a CLI command calling two use-cases.
- **Authorization decisions** — handled inside use-cases via `Principal`. Adapters construct the Principal and pass it through.
- **Cross-adapter imports** — driving adapters do not import driven adapters; driven adapters do not import each other. See [0006 — No short-circuit imports](../decisions/0006-no-short-circuit-imports.md).

## The adapter swap pattern

Every adapter swap follows the same pattern:

1. The new adapter implements the same port the old one did.
2. `composition/container.py` is changed to instantiate the new adapter instead.
3. Use-cases and services do not change.
4. The old adapter's ADR gets `status: superseded` and a `superseded-by` link to the new one's ADR.
5. The new adapter's ADR has `supersedes` pointing back.

Adapter ADRs are explicitly *expected* to be superseded over time. The port stays; the adapter rotates.

## Subfolders

- [driving/](./driving/) — CLI, HTTP API, frontend. Adapters that *call into* the core.
- [driven/](./driven/) — LLM clients, stores, indices, MCP clients. Adapters the core *calls out to*.
