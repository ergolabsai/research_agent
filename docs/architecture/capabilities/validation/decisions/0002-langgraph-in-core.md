---
id: capabilities-validation-0002
title: LangGraph is allowed in core (as coordination, not I/O)
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

[0003 — Core has no I/O](../../../decisions/0003-core-has-no-io.md) forbids I/O-touching imports in `core/`. The validation orchestrator uses LangGraph's `StateGraph` to express the 8-step sequence. LangChain (which LangGraph depends on) is normally considered an "AI orchestration library that touches I/O." This creates an apparent contradiction.

A decision is needed: is LangGraph allowed in core, or must the orchestrator be rewritten as plain Python or moved to an adapter?

## Decision

LangGraph is **allowed in core** under a strict condition: only the *coordination primitives* (`StateGraph`, `add_node`, `add_edge`, `compile`, state merging) are used. LangGraph features that themselves perform I/O — LLM calls embedded in nodes, retrieval, tool execution — are **not** invoked from core. The work each node performs goes through driven ports (`LLMClient`, `Calculator`, `PaperIndex`).

In effect: LangGraph is being used as a state machine library that happens to be from an AI ecosystem. Its I/O-capable surface is not used.

## Consequences

**Easy:**
- The orchestrator stays expressive: edges, conditional routing, and state merging are declarative and readable.
- Migrating the existing orchestrator to core is a path-level move, not a rewrite.
- LangGraph's debugging tools (graph visualization, step-by-step trace) remain available.

**Hard:**
- The "core has no I/O" rule has a documented exception. New contributors must understand the *condition* under which LangGraph is allowed, not just the package allow-list.
- LangGraph version upgrades may introduce new I/O capabilities that breach the rule by default. The team must review what is used after each upgrade.
- `import-linter` cannot, on its own, distinguish "LangGraph coordination" from "LangGraph I/O." The CI rule will allow `import langgraph` in core; reviewer judgment plus a periodic audit are the safety net.

**Forecloses:**
- LangChain's `BaseRetriever`, `LLMChain`, tool-using agents, or any LangChain class that internally constructs an I/O client — all forbidden in core. Those live in driven adapters.
- LangGraph nodes that call external services directly. A node receives its dependencies via the orchestrator's constructor (ports); it does not import a client.

## Alternatives considered

- **Rewrite the orchestrator as plain async Python or a small state machine** — viable; preserves architectural purity at the cost of expressiveness. Re-implementing LangGraph's state-merging and conditional edges by hand for a graph that will keep growing is wasted work. Reconsider if LangGraph becomes a maintenance liability.
- **Move the orchestrator to an adapter** — rejected. The orchestrator is *the core service*. Moving it to an adapter would make the entire pipeline an implementation detail rather than the system's main logic, which inverts what is and is not load-bearing.
- **Forbid LangGraph entirely in core; use a different coordination library** — viable. Workflow libraries (`prefect`, `temporal-sdk-py`) exist but bring more I/O machinery than LangGraph does. Net neutral or negative.

## Review trigger

- A LangGraph upgrade adds default behaviors that perform I/O (e.g., automatic checkpointing to disk) that the orchestrator cannot disable cleanly.
- The orchestrator stops using meaningful LangGraph features and becomes "we import LangGraph but only use the trivial parts." At that point, replacing it with ~100 lines of plain Python is cheap.
- A different coordination library appears that is closer to "state machine, nothing more" and matches the core's purity goals better.
