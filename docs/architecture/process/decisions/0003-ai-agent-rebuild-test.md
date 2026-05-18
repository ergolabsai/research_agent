---
id: process-0003
title: "Could an AI agent rebuild this file in isolation?" review check
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

[0002 — Adopt hexagonal architecture](../../decisions/0002-adopt-hexagonal-architecture.md) names AI-native development as one of the four pressures the architecture serves. The promise is: an agent rebuilding a single file should be able to do so given only the file's path, the contracts/ports it depends on, and the relevant ADRs — without reading the rest of the codebase.

This is a *property* the architecture is supposed to have. Properties decay if they are not checked. Lint rules check imports; this property requires a different check — a *reasoning* check during code review.

## Decision

When reviewing a change to `core/` (use-cases, services, domain, contracts, ports), the reviewer asks: **could a programming agent rebuild this file given only its file path, the port protocols it depends on, the contracts it uses, and the relevant ADRs?**

If the answer is "no, it also needs to know about how the CLI parses its input" or "it needs to know about Postgres' specific transaction semantics," the boundary is leaking. The reviewer flags this and either:

- The change is revised so the boundary holds, or
- An ADR captures why the leak is acceptable (rare; suggests the rule is wrong).

The check applies to `core/` because that is the layer the property is most important for. It is *also* useful for adapters (could an agent rebuild `AnthropicLLMClient` from `LLMClient` port + the Anthropic docs?), but the constraint is less strict.

## Consequences

**Easy:**
- A clear reviewer prompt that catches a class of subtle boundary violations lint rules cannot see.
- Tightens the connection between the architecture's *purpose* (bounded surface for agents) and its *enforcement* (the review).
- Catches "this use-case happens to know about HTTP status codes" — the kind of leak that compiles fine but breaches the boundary.

**Hard:**
- Subjective. Two reviewers may disagree on what an agent "needs to know." Mitigated by the ADR safety valve: when the check fires and the team disagrees, the answer is an ADR (formalize the leak or fix the boundary).
- Reviewers must internalize the check. Adding to the PR checklist ([0004](./0004-pr-review-checklist.md)) helps.

**Forecloses:**
- "It compiles, so it must be fine" reviewing of core changes.

## How to apply the check

A useful frame is: write the file in your head as `# Goal: rebuild this`, list what you'd hand the agent, and see whether the file's content actually uses only what you'd hand it. If the file pulls a knowledge that isn't on the list, that's the leak.

A failing example: a `ValidatePaper` use-case that calls `httpx.get(...)` directly to fetch a figure. The agent given only `LLMClient`, `JobStore`, `Calculator`, `PaperIndex`, `ObjectStorage` ports could not write this — they'd reach for an `ObjectStorage.get(...)` or an `ImageFetcher` port that doesn't exist. The lesson: the figure-fetch needs a port.

A passing example: a `ValidatePaper` use-case that calls only its injected dependencies, raises typed exceptions on authz failure, returns a `ValidationResult` contract, and otherwise contains business logic over the contracts. An agent given the ports and contracts could rebuild it.

## Alternatives considered

- **Strict whitelist of acceptable patterns** — rejected. Too brittle; the check works as an open-ended reviewer prompt.
- **Automated detection (e.g., AST scan for forbidden patterns)** — overlap with `import-linter`, which already catches the simple cases. The remaining cases require judgment.

## Review trigger

- The check generates more disagreement than insight — at that point either the rule needs sharpening or the architecture's contract with agents has changed.
- A class of leak appears repeatedly that the check did not catch in review. Add a lint rule for that class.
