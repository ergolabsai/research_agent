# Ports

A **port** is an interface the core declares. The core says "I need *something* that can do X"; the port describes the shape of that something. Adapters elsewhere implement the shape.

This folder is the **catalog** of all driven ports in the system. Each ADR documents one port: why it exists, its protocol signature, what kinds of adapters can satisfy it, and which adapter is currently configured.

Driving ports are not catalogued here — they are the use-cases themselves and live in the [capabilities](../capabilities/) folder. Driven ports (infrastructure the core depends on) all live here.

## How a port is structured

Every port ADR has the same anatomy:

1. **Context** — why does this port exist? What pain motivates extracting it?
2. **Decision** — the Protocol signature, given in Python type-hint form.
3. **Consequences** — what this port makes easy/hard; what it forecloses.
4. **Adapters** — list of known adapters that satisfy this port (current + alternatives).
5. **Review trigger** — when to reshape the port.

The port ADR is *not* the adapter ADR. "We have a `JobStore` port" is one decision; "we currently use SQLite for it" is a separate, supersedable decision under [adapters/driven/](../adapters/driven/).

## Ports in this system

| Port | Purpose | Current adapter |
|---|---|---|
| [`LLMClient`](./decisions/0001-llm-client-port.md) | Text and vision LLM calls | Anthropic |
| [`PaperIndex`](./decisions/0002-paper-index-port.md) | Local searchable paper corpus | LanceDB |
| [`Calculator`](./decisions/0003-calculator-port.md) | Math verification | MCP calculator server |
| [`JobStore`](./decisions/0004-job-store-port.md) | Pipeline job persistence | SQLite |
| [`ObjectStorage`](./decisions/0005-object-storage-port.md) | Large-blob storage (attachments, figures) | Local filesystem |
| [`TokenIssuer`](./decisions/0006-token-issuer-port.md) | JWT mint and verify | python-jose |
| [`PasswordHasher`](./decisions/0007-password-hasher-port.md) | Password hashing and verification | bcrypt |
| [`Clock`](./decisions/0008-clock-port.md) | Injectable time source | system clock |
| [`{Document,Workspace,User}Repository`](./decisions/0009-repository-ports.md) | Persist collaboration/identity entities | SQLite via SQLModel |

## Naming conventions

- Port names are nouns or noun phrases describing the *capability the core needs*, not the technology that will provide it. `LLMClient`, not `AnthropicClient`. `JobStore`, not `SqliteJobStore`. `PaperIndex`, not `VectorStore`.
- Methods on ports use verbs from the *core's* vocabulary: `save_job`, `get_paper`, `verify_math`. Not the adapter's vocabulary: `INSERT INTO`, `vector_search`, `calculate`.
- Async by default. Even ports that happen to be CPU-bound today should be declared `async` so the adapter has freedom; sync callers can `await` them via `asyncio.run` in narrow places, but the port shape stays async.

## Adding a port

1. A use-case or service finds it needs to talk to an external thing the core does not own.
2. Sketch the port signature: what methods does the *caller* need? Not what the adapter would naturally offer.
3. Write an ADR here using [adr-template.md](../adr-template.md). Status: `proposed`.
4. Discuss in PR; refine the signature based on review.
5. Write at least one adapter under [adapters/driven/](../adapters/driven/) with its own ADR.
6. Accept the port ADR and the adapter ADR together.
