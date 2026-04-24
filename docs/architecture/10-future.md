# Conceptual Future Architectures

This project is pre-alpha. The goal of this doc is not to commit to anything — it's to sketch a few plausible shapes we might grow into, so the architect has concrete options to push back on or combine.

Three sketches, from most-conservative to most-ambitious.

---

## A) Minimal-lift launch ("what we have, production-ready")

Keep the current architecture almost verbatim. Fix the known issues, harden security, add observability. No rewrites.

```mermaid
---
config:
  theme: neo-dark
  look: neo
  layout: elk
---
flowchart LR
    subgraph Users["Users"]
        Web["Web app"]
    end

    subgraph Edge["Edge"]
        CDN["Static CDN"]
        WAF["WAF / rate limit"]
    end

    subgraph App["App tier"]
        API["FastAPI<br/>(2+ replicas)"]
        Worker["Pipeline worker<br/>(in-proc today,<br/>queue-driven tomorrow)"]
        MCP["Calculator MCP<br/>(SSE)"]
    end

    subgraph Data["Managed data"]
        PG[("Postgres")]
        S3[("S3 / MinIO")]
        Lance[("LanceDB<br/>(read-only)")]
    end

    subgraph Ext["External"]
        Claude["Anthropic"]
        SS["Semantic Scholar"]
    end

    subgraph Obs["Observability"]
        Logs["Structured logs<br/>(Loki / Datadog)"]
        Metrics["Metrics<br/>(Prometheus)"]
        Trace["Tracing<br/>(OpenTelemetry)"]
    end

    Web --> CDN
    Web --> WAF --> API
    API --> PG
    API --> S3
    API --> Worker
    Worker --> PG
    Worker --> S3
    Worker --> Lance
    Worker --> MCP
    Worker --> Claude
    Worker --> SS
    App --> Obs
```

**Changes from today:**

- CORS locked to known origins.
- `/users/search` behind auth.
- Postgres instead of SQLite.
- Pipeline extracted into a worker behind a small queue (Arq / RQ).
- MCP Calculator as an SSE service (not stdio per pipeline).
- Rate limiting on `/pipeline/validate` (cost control).
- Structured logging + basic metrics + OpenTelemetry traces.
- Secrets via managed secret store.

**Trade-offs:** Ships fast. Preserves the LangGraph + agent shape. Doesn't solve latency (serial pipeline) or extensibility (hard to add new agents / new interfaces).

---

## B) Multi-interface, agent-first ("the shape implied by the user's original sketch")

Reshape around the original diagram the user drew: multiple interfaces (web, extension, mobile, Drive), a unified API, a general-purpose router agent that dispatches to specialists, and pluggable MCP servers.

```mermaid
---
config:
  theme: neo-dark
  look: neo
  layout: elk
---
flowchart LR
    subgraph Interfaces["Interfaces"]
        Web["Web app"]
        Ext["Browser extension"]
        Mobile["Mobile app"]
        Drive["Google Drive /<br/>Dropbox integrations"]
    end

    subgraph API["Unified API"]
        Auth["Auth"]
        Users["User data"]
        State["Workflow state<br/>+ job queue"]
        HIL["Human-in-the-loop<br/>(approvals, edits)"]
    end

    subgraph AgentRuntime["Agent runtime"]
        Router["General / Router Agent"]
        Logic["Logic Agent"]
        Math["Math Agent"]
        Figure["Figure Agent"]
        Lib["Librarian Agent"]
        Final["Assemble Results"]
    end

    subgraph MCP["MCP servers (pluggable)"]
        MathMCP["Math MCP"]
        PlotMCP["Plot MCP"]
        CiteMCP["References/Citations MCP"]
        ArxivMCP["arXiv MCP"]
    end

    subgraph Repos["Code / data repos"]
        Numpy["NumPy / SciPy"]
        Plotting["Plotting tools"]
    end

    subgraph arXiv["arXiv"]
        Meta["Metadata"]
        Papers["Papers"]
    end

    DB[("User DB")]
    Files[("Artifacts &<br/>documents")]

    Web --> API
    Ext --> API
    Mobile --> API
    Drive --> API

    API --> Router
    API --> DB
    API --> Files
    API <--> HIL

    Router --> Logic
    Router --> Math
    Router --> Figure
    Router --> Lib
    Router --> Final

    Logic --> CiteMCP
    Math --> MathMCP
    Figure --> PlotMCP
    Lib --> ArxivMCP

    MathMCP --> Numpy
    PlotMCP --> Plotting
    CiteMCP --> Meta
    ArxivMCP --> Meta --> Papers
```

**Why:** Matches the product story the user already has. Decouples interfaces (a browser extension that validates a paper on arXiv is a natural fit). Agents become swappable, not baked into LangGraph nodes.

**Changes from today:**

- LangGraph orchestrator becomes a **router agent** that decides which specialists to call, possibly in parallel. Logic/Math/Figure/Librarian become tool-using agents behind the same MCP abstraction.
- Explicit human-in-the-loop primitives on the API — the current "job runs to completion" model becomes "job pauses on a question, resumes on user input."
- Interfaces multiply. The API surface stays stable.
- Pluggable MCP registry — new validators (plots, stats, chemistry) show up as new servers without touching the router.

**Trade-offs:** Bigger lift. More moving parts. Router-agent reliability is a real concern (we'd need strong guardrails). Latency could *improve* if specialists run in parallel.

---

## C) Graph-native, evidence-first ("the knowledge graph is the product")

Take seriously that the paper graph *is* the real output. Build the whole system around incremental graph construction, with agents as producers/consumers of typed graph nodes, and the UI as a graph editor.

```mermaid
---
config:
  theme: neo-dark
  look: neo
  layout: elk
---
flowchart LR
    subgraph Clients["Clients"]
        Browser["Graph-first UI<br/>(edit, annotate, explore)"]
        Agents2["Agent clients<br/>(web, ext, mobile)"]
    end

    subgraph API["API"]
        GraphAPI["Graph API<br/>(nodes/edges CRUD +<br/>subscriptions)"]
        AuthSvc["Auth / sharing"]
    end

    subgraph Graph["Graph store (core)"]
        Nodes[("Typed nodes:<br/>paper, step, evidence,<br/>figure, math, related_paper,<br/>assertion, rebuttal")]
        Edges[("Typed edges:<br/>HAS_STEP, DEPENDS_ON,<br/>SUPPORTS, ASSESSES,<br/>RELATED_TO, CONTRADICTS")]
    end

    subgraph Producers["Producers (agents)"]
        Ingest["Ingestion agent<br/>(paper → steps)"]
        Evidence["Evidence agent"]
        FigureA["Figure agent"]
        MathA["Math agent"]
        LibA["Librarian agent"]
        ReviewA["Reviewer agent<br/>(writes assertions)"]
    end

    subgraph Consumers["Consumers"]
        Report["Report generator"]
        Exporter["Export<br/>(LaTeX/PDF/arXiv)"]
        Timeline["Activity timeline"]
    end

    subgraph Infra["Infra"]
        Events["Event log<br/>(Kafka / NATS / Postgres LISTEN)"]
        BlobStore[("Object storage")]
        VectorDB[("Vector DB<br/>for embeddings")]
    end

    Clients --> GraphAPI
    GraphAPI --> Graph
    GraphAPI --> Events

    Events --> Producers
    Producers --> Graph
    Producers --> BlobStore
    Producers --> VectorDB

    Consumers --> Graph
    Clients --> Consumers
```

**Why:** The paper graph already exists as a side product. Making it the primary artifact means:

- Agents become independent producers that react to graph changes (evidence added → figure agent wakes up).
- Users can edit the graph directly — annotate a step, add a counter-example, attach a new citation — and the downstream graph updates.
- Reruns are cheap: invalidate one node, replay only what depends on it.
- Reviewer / advisor / co-author workflows become natural: multiple humans + multiple agents editing the same graph.

**Changes from today:**

- The rigid 8-step linear pipeline goes away. Replaced by event-driven agents subscribing to graph changes.
- Storage becomes a graph (Postgres with adjacency tables is fine; Neo4j is overkill at this stage).
- The UI becomes graph-first — the current markdown review is generated from the graph, not stored alongside it.
- Job state becomes "the graph plus an activity log" — no more `PipelineJob.status`.

**Trade-offs:** Biggest rewrite. Highest conceptual clarity if it works. Graph editors are hard to build well. Consistency/race-condition risk across agents writing to the same graph.

---

## How to decide

| Question                                                      | Pushes toward |
| ------------------------------------------------------------- | ------------- |
| "Is validation a one-shot or a workflow?"                     | One-shot → A; workflow → B or C |
| "Do users want to edit the evidence graph?"                   | Yes → C       |
| "Do we want a browser extension or Drive integration in v1?"  | Yes → B       |
| "How much engineering budget do we have for launch?"          | Low → A; medium → B; high → C |
| "Is the graph a byproduct or the product?"                    | Product → C   |
| "How important is parallelism / latency?"                     | Critical → B or C |

## Things that don't change across all three

- **The LLM boundary** — Anthropic-via-LangChain + MCP tools is a good bet regardless of shape.
- **The evidence taxonomy** — typed nodes/edges (step, evidence, figure, math, related_paper) are worth keeping.
- **Per-step auditability** — wherever reasoning happens, we should be able to show the user what was sent, what came back, and why the conclusion was reached.
- **Pluggable knowledge sources** — LanceDB today, maybe Qdrant tomorrow; Semantic Scholar today, maybe OpenAlex or S2-plus tomorrow. The Librarian abstraction shouldn't care.

## Open questions for the architect

- Is the product "a validation report" or "a living evidence graph"? That single answer changes everything.
- Is "one paper at a time" enough, or do we need workspace/project-level cross-paper validation (e.g., "does this paper contradict anything else in our workspace")?
- Who owns the graph — the author, the advisor, or the reviewer? Access control implications cascade through all three shapes.
- How much of the pipeline do we want to be steerable by the user (e.g., "focus on math, skip figures this run")?
