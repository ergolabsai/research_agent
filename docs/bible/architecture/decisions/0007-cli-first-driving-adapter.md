---
id: architecture-0007
title: CLI is the first-class driving adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The project will grow several driving adapters: the existing HTTP API and React frontend, a CLI, eventually a desktop GUI, and connector-style integrations. The order in which features are exposed through these adapters shapes how features are designed.

If features ship to the API first, the API becomes the de-facto specification of "what the system does." Other adapters end up *translating from* the API rather than *invoking* the core. The API's idioms (HTTP status codes, request/response shapes, middleware) leak into how the system is reasoned about.

A different ordering is available, and it has consequences.

## Decision

When a new use-case is built, it is wired to the **CLI first**, then to the API and other driving adapters. The CLI is treated as the *first-class* driving adapter — the one that is always up-to-date with the use-case layer.

The CLI does not get features the API does not have. It gets features *first*. Other adapters follow in the same PR or a closely-following PR.

## Consequences

**Easy:**
- AI coding agents have a uniform testing backbone. A CLI invocation is the closest thing to "what a user would do" that an agent can run without a browser, a server, or HTTP mocking. `advisor <command> --json` is the agent's preferred surface.
- Every feature has a scriptable form by default. Internal automation, replay tools, and CI fixtures use the CLI rather than direct database manipulation.
- The CLI surfaces design problems early: if a feature is awkward to expose as a command, it is probably awkward as an API endpoint too.
- The use-case layer stays the source of truth, not the API. The CLI is a thin shell around it; if the CLI requires duplicating logic, the boundary is wrong.

**Hard:**
- Slightly more work per feature: every PR adds at least a CLI command in addition to whatever else.
- The CLI must be kept genuinely usable, including help text, exit codes, and `--json` output for agent consumption. This is an ongoing UX commitment.

**Forecloses:**
- "Internal-only" features that have no CLI. Internal features get a CLI command (possibly hidden behind a dev flag — see [0008](./0008-one-binary-role-gated.md)). They do not skip the CLI layer.
- The CLI being a thin afterthought tracked in a separate sprint.

## Critical clarification

The CLI does **not** get features first; the **use-case layer** does. The CLI is simply the first adapter to expose the use-case. This distinction matters: a feature does not exist until its use-case exists and is tested at the core level. The CLI is then a thin shell around it.

## Alternatives considered

- **API-first** — rejected. Makes the API the spec; other adapters become translations. Also makes AI-agent testing harder: agents need a running server, HTTP client, and auth setup to exercise a feature, instead of a single `advisor` invocation.
- **GUI-first** — rejected. The GUI is the slowest adapter to write and the hardest to test programmatically. Putting it first slows every feature.
- **No adapter ordering; whichever is convenient** — rejected. Conveniently-ordered adapters end up with a primary one anyway, and the choice is implicit. Better to choose explicitly.

## Review trigger

- The CLI becomes a maintenance burden that pulls focus from the API or use-cases — e.g., disproportionate time spent on CLI UX polish. The CLI should be uniform and predictable, not beautiful.
- A non-CLI surface (GUI, browser extension) becomes the dominant user channel by a large margin, and the CLI's first-class status starts feeling vestigial. At that point the rule may shift, but the *order* still matters; pick the new first-class adapter deliberately.
