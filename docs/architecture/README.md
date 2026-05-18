# Architecture

This folder is the canonical place where every architectural choice in Research Advisor is recorded, named, and statusable. If a decision matters, it lives here. If it doesn't live here, it isn't a decision — it's an opinion someone had at a keyboard.

## How to read this

Three artifact kinds with separate lifecycles:

1. **System docs** (`*/README.md`) — descriptive. "What this thing is, conceptually." Updates when the *shape* of the system changes. Framework-free where possible.
2. **ADRs** (`decisions/NNNN-*.md` and `*/decisions/NNNN-*.md`) — propositional. "We chose X because Y. Alternatives were Z. Status: accepted." Status changes by writing a *new* ADR that supersedes the old one, never by editing the old one.
3. **Known issues** ([KNOWN_ISSUES.md](./KNOWN_ISSUES.md)) — short, tracker-style. Bugs and partial implementations. Each item either earns an ADR (if it implies a decision) or gets fixed (if it doesn't).

What is deliberately **not** here:

- A "current state" living document. Code is the current state; ADRs explain why it looks that way.
- A TODO list. Belongs in PRs or a tracker.

## If you're new to the project

Read these umbrella ADRs in order — they describe the shape of the whole system, and every other decision in this folder rests on them:

1. [0002 — Adopt hexagonal architecture](./decisions/0002-adopt-hexagonal-architecture.md) — the load-bearing decision. Everything else follows.
2. [0003 — Core has no I/O](./decisions/0003-core-has-no-io.md) — the rule that keeps the hexagon from collapsing.
3. [0005 — Principal in every use-case](./decisions/0005-principal-in-every-usecase.md) — how authorization flows.
4. [0009 — Composition is the only wiring layer](./decisions/0009-composition-as-only-wiring.md) — how the pieces get connected.

## Folder map

| Folder | What lives here |
|---|---|
| [decisions/](./decisions/) | Cross-cutting architectural decisions — hexagonal, ports as protocols, composition, the umbrella rules. The shape of the whole system. |
| [capabilities/](./capabilities/) | Domain capabilities the system offers, framework-free. `validation`, `collaboration`, `identity`, `knowledge`. |
| [ports/](./ports/) | The interface contracts the core declares. One ADR per port. |
| [adapters/](./adapters/) | Concrete implementations: which library, which provider, which database. Driving (CLI, API, frontend) and driven (LLM, store, index). |
| [infrastructure/](./infrastructure/) | How the system runs. Outside the hexagon. Docker, nginx, deploy targets. |
| [frontend/](./frontend/) | The React app — itself a driving adapter, but with enough of its own decisions to warrant a folder. |
| [process/](./process/) | How we *work*, not what we build. CI gates, review checklists, ADR practice itself. |

## Umbrella ADRs (top-level `decisions/`)

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

Scoped ADRs (one capability, one port, one adapter, etc.) live in the relevant subfolder's own `decisions/`.

## Migration

Time-bound work to move from the current code to the architecture described here: [MIGRATION.md](./MIGRATION.md).

## Status legend

Every ADR has a `status` field in its frontmatter. Allowed values:

- **proposed** — written down, not yet committed. Open for debate. May never land.
- **accepted** — current state of the system. Changing this requires a *new* ADR that supersedes it.
- **deprecated** — no longer the recommended approach, but still present in code. New work should not adopt it.
- **superseded** — replaced by another ADR. Kept for history; links forward to the replacement.

Mapping from informal vocabulary:

- **flexible** → `accepted` with an explicit *Alternatives considered* section listing acceptable swap-ins, plus a `Review trigger`.
- **open** → `proposed`.
- **planned** → `proposed` with a note that it's a forward bet, not a current implementation.

This avoids inventing a non-standard taxonomy.

## How to propose a change

1. Copy [adr-template.md](./adr-template.md) into the right `decisions/` folder.
2. Number it: next available `NNNN-` in that folder.
3. Set `status: proposed`.
4. Fill in Context, Decision, Consequences, Alternatives considered, Review trigger.
5. Open a PR. Discussion happens in the PR.
6. If accepted: change `status` to `accepted` and merge. If accepted *and* it replaces something: update the predecessor's `status` to `superseded` and add cross-links in `supersedes` / `superseded-by`.
7. If rejected: merge anyway with `status: proposed` and a note in the body explaining the rejection, *or* close without merging. Both are defensible. Closing without merging means the reasoning is lost to PR history — keep this in mind.

See [process/0002 — ADR authoring and lifecycle](./process/decisions/0002-adr-process.md) for the full workflow.

## How to read an ADR

If you have 30 seconds: read the title and `status`.
If you have 2 minutes: read `Decision` and `Review trigger`.
If you have 10 minutes: read the whole thing, especially `Alternatives considered` — that's where the *interesting* reasoning lives.

## Code references

Cross-cutting and capability-level ADRs (under `decisions/`, `capabilities/`, `ports/`) deliberately avoid code references — they describe rules and concepts that outlive any specific commit.

Adapter, infrastructure, and frontend ADRs may cite current implementation files at the *path* level (e.g., "current implementation: `advisor_pipeline/llm.py`"). They never cite line numbers; those drift within a single commit.

Line-precision pointers into current code live in [MIGRATION.md](./MIGRATION.md) — a time-bound document that gets archived when the migration completes.

## Glossary

- **Core** — the pure-Python hexagon. No I/O. No web framework, no DB driver, no SDK. Contains contracts, domain, services, use-cases, ports.
- **Use-case** — a single user intent expressed as a callable (e.g., `ValidatePaper`). One file. Takes `Principal` as first argument. The only way into the core.
- **Port** — an interface (`typing.Protocol`) that the core declares. *Driving* ports are use-case signatures. *Driven* ports are infrastructure interfaces.
- **Adapter** — a concrete implementation. *Driving* adapters call into use-cases (CLI, API, frontend). *Driven* adapters implement driven ports (LLM client, job store, etc.).
- **Composition** — the wiring layer. The only place that imports across the boundary. Constructs adapters, injects them into use-cases.
- **Principal** — a value object carrying the identity and roles of whoever invoked a use-case. Constructed at the adapter boundary; flows through every use-case.
- **Capability** — a domain area of functionality (`validation`, `collaboration`, etc.). A capability has use-cases, may have services and domain entities, and depends on ports.
