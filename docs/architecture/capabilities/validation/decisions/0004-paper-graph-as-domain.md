---
id: capabilities-validation-0004
title: Paper graph is a domain entity, not an adapter concern
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The validation pipeline builds a typed graph of papers, logical steps, evidence, figures, math, and related papers, connected by supports/contradicts/cites edges. Many post-validation analyses are graph queries: "which steps have no evaluation?", "which figures contradict their claims?", "which related papers converge with the submitted paper?"

NetworkX is the library used today. It is pure Python, no I/O. The question is *where* the graph and its query helpers live: in the core as a domain entity, in an adapter as a "graph adapter," or split between contracts (the data) and a service (the queries).

## Decision

The paper graph lives in **core as a domain entity** (`core/domain/graph.py`). It encapsulates:

- The graph data structure (a NetworkX `DiGraph` with typed nodes and edges).
- The construction helper (`build_graph_from_validation(result) -> PaperGraph`).
- The query methods (`get_contradicted_steps`, `get_invalid_math`, `get_steps_with_no_evidence`, etc.).

The graph is *not* persisted by the domain — persistence is via the `JobStore` port (which serializes via `nx.node_link_data` to JSON). The graph is *not* an adapter — it has no I/O and no infrastructure dependency.

## Consequences

**Easy:**
- Use-cases and services pass the `PaperGraph` around as a regular Python object. Queries are method calls, not service calls.
- The graph is testable in isolation — construct one from a fixture `ValidationResult`, assert on query results.
- NetworkX is a pure-Python coordination library, allowed in core by [0003 — Core has no I/O](../../../decisions/0003-core-has-no-io.md).

**Hard:**
- Serialization for storage (via `JobStore`) is JSON-of-`node_link_data`. The `JobStore` adapter must understand this format. Mitigation: keep the serialization helpers next to the graph code; the adapter calls them rather than re-implementing.
- The graph is constructed *after* the pipeline completes. There is no "live" graph during pipeline execution — that is a deliberate simplification.

**Forecloses:**
- Storing the graph in a graph database (Neo4j, Memgraph) as the canonical form. Today the graph is *derived* from the `ValidationResult`; it is not the source of truth. Persistence in a graph DB would be a future ADR if "querying across jobs" becomes important.
- Treating graph queries as ad-hoc functions floating in `core/`. They are methods on the graph entity so the contract stays cohesive.

## Alternatives considered

- **Graph as an adapter concern, wrapped behind a port** — rejected. The graph has no I/O; wrapping it in a port would be ceremony with no benefit.
- **Graph queries scattered as free functions in `core/services/`** — rejected. The queries operate on graph state; they belong as methods. Free functions in services are reserved for orchestration across multiple ports.
- **Replace NetworkX with a hand-rolled adjacency map** — rejected. NetworkX is mature, pure-Python, and the queries lean on its algorithms. Replacing it would re-implement standard graph operations badly.

## Review trigger

- The graph needs to be queried *across* validation jobs (e.g., "papers that contradict this one across all runs"). At that point a persistent graph store becomes warranted, and the in-memory NetworkX object becomes a projection of that store.
- NetworkX becomes a performance bottleneck on very large graphs (unlikely at single-paper scale; possible if graphs span many papers).
