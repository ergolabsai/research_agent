# Architecture

Cross-cutting decisions about the *shape* of the whole system. The umbrella under which every capability, port, adapter, and infrastructure choice sits.

If you're new to the project, read these in order:

1. [0002 — Adopt hexagonal architecture](./decisions/0002-adopt-hexagonal-architecture.md) — the umbrella decision. Everything else follows from this.
2. [0003 — Core has no I/O](./decisions/0003-core-has-no-io.md) — the rule that keeps the hexagon from collapsing.
3. [0005 — Principal in every use-case](./decisions/0005-principal-in-every-usecase.md) — how authorization flows.
4. [0009 — Composition is the only wiring layer](./decisions/0009-composition-as-only-wiring.md) — how the pieces get connected.

The rest are supporting rules.

## ADRs in this folder

| # | Title | Status |
|---|---|---|
| [0001](./decisions/0001-use-madr-format.md) | Use MADR format for ADRs | accepted |
| [0002](./decisions/0002-adopt-hexagonal-architecture.md) | Adopt hexagonal architecture | accepted |
| [0003](./decisions/0003-core-has-no-io.md) | Core has no I/O | accepted |
| [0004](./decisions/0004-ports-as-protocols.md) | Ports are `typing.Protocol`, not ABCs | accepted |
| [0005](./decisions/0005-principal-in-every-usecase.md) | `Principal` flows through every use-case | accepted |
| [0006](./decisions/0006-no-short-circuit-imports.md) | No short-circuit imports across layers | accepted |
| [0007](./decisions/0007-cli-first-driving-adapter.md) | CLI is the first-class driving adapter | accepted |
| [0008](./decisions/0008-one-binary-role-gated.md) | One CLI binary, role-gated commands | accepted |
| [0009](./decisions/0009-composition-as-only-wiring.md) | Composition is the only wiring layer | accepted |
| [0010](./decisions/0010-single-pyproject-with-linter.md) | Single `pyproject.toml` with `import-linter` | accepted |
| [0011](./decisions/0011-single-repo-for-now.md) | Single repo, defer splitting | accepted |
| [0012](./decisions/0012-no-di-framework.md) | No DI framework | accepted |

## Migration

Time-bound work to move from the current code to the architecture described here: [MIGRATION.md](./MIGRATION.md).
