# The Bible

This is the canonical place where every architectural choice in Research Advisor is recorded, named, and statusable. If a decision matters, it lives here. If it doesn't live here, it isn't a decision — it's an opinion someone had at a keyboard.

## How to read this

The bible has three artifact kinds with separate lifecycles:

1. **System docs** (`*/README.md`) — descriptive. "What this thing is, conceptually." Updates when the *shape* of the system changes. Framework-free where possible.
2. **ADRs** (`*/decisions/NNNN-*.md`) — propositional. "We chose X because Y. Alternatives were Z. Status: accepted." Status changes by writing a *new* ADR that supersedes the old one, never by editing the old one.
3. **Known issues** ([KNOWN_ISSUES.md](./KNOWN_ISSUES.md)) — short, tracker-style. Bugs and partial implementations. Each item either earns an ADR (if it implies a decision) or gets fixed (if it doesn't).

What is deliberately **not** here:

- A "current state" living document. Code is the current state; ADRs explain why it looks that way.
- A TODO list. Belongs in PRs or a tracker.

## Folder map

| Folder | What lives here |
|---|---|
| [architecture/](./architecture/) | Cross-cutting structural decisions — hexagonal, ports, composition, the umbrella rules. The shape of the whole system. |
| [capabilities/](./capabilities/) | Domain capabilities the system offers, framework-free. `validation`, `collaboration`, `identity`, `knowledge`. |
| [ports/](./ports/) | The interface contracts the core declares. One ADR per port. |
| [adapters/](./adapters/) | Concrete implementations: which library, which provider, which database. Driving (CLI, API, frontend) and driven (LLM, store, index). |
| [infrastructure/](./infrastructure/) | How the system runs. Outside the hexagon. Docker, nginx, deploy targets. |
| [frontend/](./frontend/) | The React app — itself a driving adapter, but with enough of its own decisions to warrant a folder. |
| [process/](./process/) | How we *work*, not what we build. CI gates, review checklists, ADR practice itself. |

## Status legend

Every ADR has a `status` field in its frontmatter. Allowed values:

- **proposed** — written down, not yet committed. Open for debate. May never land.
- **accepted** — current state of the system. Changing this requires a *new* ADR that supersedes it.
- **deprecated** — no longer the recommended approach, but still present in code. New work should not adopt it.
- **superseded** — replaced by another ADR. Kept for history; links forward to the replacement.

The user's earlier vocabulary of "flexible / open / planned" maps cleanly:

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

## How to read an ADR

If you have 30 seconds: read the title and `status`.
If you have 2 minutes: read `Decision` and `Review trigger`.
If you have 10 minutes: read the whole thing, especially `Alternatives considered` — that's where the *interesting* reasoning lives.

## Code references

ADRs in `architecture/` and `capabilities/` and `ports/` deliberately avoid code references — they describe rules and concepts that outlive any specific commit.

ADRs in `adapters/`, `infrastructure/`, and `frontend/` may cite current implementation files at the *path* level (e.g., "current implementation: `advisor_pipeline/llm.py`"). They never cite line numbers; those drift within a single commit.

Line-precision pointers into current code live in [architecture/MIGRATION.md](./architecture/MIGRATION.md) — a time-bound document that gets archived when the migration completes.

## Glossary

- **Core** — the pure-Python hexagon. No I/O. No web framework, no DB driver, no SDK. Contains contracts, domain, services, use-cases, ports.
- **Use-case** — a single user intent expressed as a callable (e.g., `ValidatePaper`). One file. Takes `Principal` as first argument. The only way into the core.
- **Port** — an interface (`typing.Protocol`) that the core declares. *Driving* ports are use-case signatures. *Driven* ports are infrastructure interfaces.
- **Adapter** — a concrete implementation. *Driving* adapters call into use-cases (CLI, API, frontend). *Driven* adapters implement driven ports (LLM client, job store, etc.).
- **Composition** — the wiring layer. The only place that imports across the boundary. Constructs adapters, injects them into use-cases.
- **Principal** — a value object carrying the identity and roles of whoever invoked a use-case. Constructed at the adapter boundary; flows through every use-case.
- **Capability** — a domain area of functionality (`validation`, `collaboration`, etc.). A capability has use-cases, may have services and domain entities, and depends on ports.
