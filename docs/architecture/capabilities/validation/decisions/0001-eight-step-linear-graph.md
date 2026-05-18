---
id: capabilities-validation-0001
title: Eight-step linear validation pipeline
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The validation pipeline performs several distinct kinds of analysis: enriching the paper with context, gathering related work, mapping logical structure, finding evidence per step, evaluating figures, verifying math, scoring related papers, and compiling results.

These could be expressed as a fan-out DAG (figures, math, and evidence could run in parallel), as an event-driven workflow, or as a linear sequence. Each choice trades latency against operational complexity and debuggability.

## Decision

The pipeline is a **linear sequence of 8 steps**, expressed as a LangGraph `StateGraph` with one edge per transition:

```
make_context → gather_papers → map_logic → find_evidence → evaluate_figures → evaluate_math → score_papers → compile_results
```

State flows through an `AdvisorState` TypedDict. Each step is a node; each node returns a state update that the framework merges into the running state.

## Consequences

**Easy:**
- The pipeline is trivially debuggable: every node has a known predecessor, and the state at any point is determined by replaying earlier steps.
- Per-step logging and progress reporting are natural — there is one "current step" at any moment.
- Adding a step is a one-line edge change; reordering is a few-line change.
- A step callback (e.g., for progress UI) sees exactly one event per step.

**Hard:**
- Steps that *could* run in parallel (figures and math are independent) currently run serially. End-to-end latency is higher than necessary.
- The linear shape encourages "stuff one more thing into the next step" rather than designing a new node — there is a soft drift toward overloaded steps over time.

**Forecloses:**
- Parallel figure and math evaluation. Deferred until end-to-end latency becomes a binding concern.
- Streaming partial results to the client as steps complete (the API model is still "submit, poll, receive"). Possible later via the step callback; not now.

## Alternatives considered

- **Fan-out DAG (figures and math in parallel after `map_logic`)** — viable. Saves ~30–40% latency for papers with many figures. Deferred because (a) current LLM rate limits dominate latency anyway, and (b) parallel state-merging adds complexity that has not yet paid off.
- **Event-driven workflow (each step emits an event; subscribers process in any order)** — rejected. Overkill at current scale. Reintroduces the operational complexity hexagonal architecture is trying to keep simple.
- **One monolithic LLM call ("here is the paper, return everything")** — rejected. Quality degrades sharply; per-step prompts allow per-step optimization and per-step retry.

## Review trigger

- End-to-end validation latency exceeds the user's tolerance budget (currently unset; pick a number when this becomes user-visible).
- A step is added that genuinely doesn't fit the linear shape (e.g., a "request human review" branch that pauses indefinitely). At that point the linear assumption breaks and a DAG is warranted.
