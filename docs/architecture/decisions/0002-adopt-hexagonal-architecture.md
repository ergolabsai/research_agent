---
id: architecture-0002
title: Adopt hexagonal architecture (Ports and Adapters)
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The project is moving from a working prototype onto a dedicated server, and several pressures converge at the same time:

- **Multiple future driving surfaces.** Beyond the current React frontend and FastAPI backend, the project will need a first-class CLI, a desktop GUI eventually, and connector-style integrations (browser extensions, document-suite plugins).
- **AI-native development.** Parts of the system will be rebuilt repeatedly with many programming agents working in parallel. Agents work best against bounded, contract-defined surface area.
- **Multiple teams, shared ownership.** 3–5 people split across frontend, backend, and pipeline concerns. Independent deploy lifecycles are desirable: rolling the pipeline forward should not require redeploying the API.
- **Real scale eventually.** More concurrent users and longer pipelines. In-process thread pools and embedded SQLite will not survive.

The current code couples the backend to the pipeline at the import level, shares one editable Python package, and has no seam between "what the system does" and "how it is invoked." That coupling is the obstacle to all four pressures above.

## Decision

Adopt **Hexagonal Architecture** (Alistair Cockburn, 2005), also called **Ports and Adapters**. Structure the system around a pure **core** that contains business logic and knows nothing about the outside world. The core defines two kinds of interface:

- **Driving ports** — what the core *offers*. These are use-cases. External callers (CLI, HTTP API, GUI) invoke them.
- **Driven ports** — what the core *needs*. These are protocols for infrastructure (job store, LLM client, paper index, object storage, clock). External infrastructure implements them.

Adapters live on both sides: driving adapters translate the outside world into use-case calls; driven adapters implement the protocols the core depends on.

## Consequences

**Easy:**
- Each new driving surface (CLI, browser extension, etc.) is a thin translation layer over existing use-cases. No business-logic duplication.
- Infrastructure swaps (SQLite → Postgres, Anthropic → OpenRouter) are configuration changes in the composition layer.
- Use-cases are testable with fake adapters in milliseconds. Real-infrastructure tests live in adapter-specific integration tests.
- Independent deploy lifecycles become possible: driving adapters and driven adapters can be packaged separately. The boundary exists in code, not just in plan documents.
- AI agents can be scoped to a single port + adapter — rebuilding the LanceDB adapter means reading one protocol file and one implementation file.

**Hard:**
- More files, more indirection. A "just call this function" path becomes "call this use-case, which calls this service, which calls this port."
- Discipline required: the architecture decays the moment anyone takes a short-circuit shortcut.
- Initial migration is real work, not just a folder rename — singletons must become injected dependencies, direct imports must become protocol calls.

**Forecloses:**
- "Just add a quick endpoint that does X directly" — the right answer is always "add a use-case, then expose it."
- Treating the LLM, the database, or any external system as a casually-available global.

## Alternatives considered

- **Layered (n-tier) architecture** — rejected. Layered architecture allows any layer to know about the one below it, which lets the API know about Postgres specifics. Hexagonal flips this: the core does not know what is below it because there is no "below" — only the port surface.
- **Clean Architecture / Onion Architecture** — viable; nearly identical in intent. Hexagonal is preferred for its vocabulary ("ports," "adapters") which is concrete enough to enforce in code review and CI lint rules.
- **Modular monolith without hexagonal seams** — rejected. The pressure for a CLI and for AI-agent-scoped rebuilds requires a protocol surface, not just module boundaries.
- **Microservices from day one** — rejected. Premature. Adds operational complexity (cross-service contracts, deployment coordination, distributed tracing) before the team is large enough to absorb it.

## Review trigger

- The team consistently bypasses the hexagonal boundary in ways that lint rules cannot catch (smuggling infrastructure types through `Any`, importing adapters via dynamic loading) — a sign the rules are out of step with how people actually work.
- A different architecture (event-sourced, actor-model, etc.) becomes a better fit for the dominant workload — e.g., if the system becomes primarily an event-stream processor rather than a request/response service.
