# Capabilities

A **capability** is a domain area of functionality that the system offers. Capabilities are described framework-free: they would still be capabilities if the system were rewritten in a different language.

Each capability has:

- A **README** describing what it does, what its key concepts are, and what use-cases it exposes.
- A `decisions/` folder for ADRs scoped to that capability — e.g., "the validation pipeline is 8 sequential steps."

Capabilities **do not** describe HTTP endpoints, CLI commands, or database schemas. Those are adapter and infrastructure concerns. A capability says *what the system does for the user*; adapters describe *how that capability is reached*.

## Why capabilities, not current-system folders

An earlier draft of the docs organized by current code structure: `frontend/`, `backend/`, `pipeline/`. That mirroring made sense for descriptive docs but breaks under hexagonal architecture, where the code reorganizes into `core/`, `adapters/`, `composition/` — orthogonal to what the system *does*.

Capabilities survive both: validation is a capability whether the orchestrator lives in `advisor_pipeline/` or `core/services/`. Identity is a capability whether passwords are bcrypt or argon2. Organizing docs by capability makes the docs robust to architectural change.

See [0002 — Adopt hexagonal architecture](../decisions/0002-adopt-hexagonal-architecture.md) for the underlying choice.

## Capabilities in this project

| Capability | What it does |
|---|---|
| [validation/](./validation/) | Validate a scientific paper end-to-end: parse logical structure, find evidence, verify math, evaluate figures, score related work, produce a confidence assessment. |
| [collaboration/](./collaboration/) | Notion-like workspace and document model. Users create documents, organize them in workspaces, share them, and track edits. |
| [identity/](./identity/) | Authentication and authorization. Registration, login, password handling, JWT issuance, guest-try flow, the `Principal` value object. |
| [knowledge/](./knowledge/) | The system's view of "what papers exist out there." Maintains a searchable index (currently arXiv via LanceDB; eventually broader) and routes lookups through a `PaperIndex` port. |

## What a capability is *not*

- Not a microservice. Capabilities are conceptual, not deployment artifacts. Multiple capabilities live in one Python process today; they may split later if independent scaling is needed.
- Not a team boundary, necessarily. Teams may own multiple capabilities or share one. The boundary is functional, not organizational.
- Not a port or adapter. Capabilities *use* ports and *depend on* adapters being configured. The ports themselves catalog in [ports/](../ports/); the adapters in [adapters/](../adapters/).

## Adding a new capability

1. Create `capabilities/{name}/README.md` describing what it does in framework-free terms.
2. Create `capabilities/{name}/decisions/` for ADRs scoped to that capability.
3. Add an entry to the table above.
4. New use-cases that fit the capability live in `core/use_cases/{name}/` once the migration is complete.
