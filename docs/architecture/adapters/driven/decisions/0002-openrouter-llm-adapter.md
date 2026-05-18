---
id: adapters-driven-0002
title: OpenRouter as an alternative `LLMClient` adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

A second `LLMClient` adapter is desirable for two reasons:

1. **Provider portability** — having an alternative working at any time keeps the team from quietly drifting into single-vendor lock-in.
2. **Experimentation** — OpenRouter aggregates many providers and models behind one API, making per-call provider/model swaps cheap.

OpenRouter is a third-party router; using it as the *default* has trade-offs (extra hop, separate billing relationship, dependency on a routing layer). Using it as an *alternative* is low-cost.

## Decision

Implement `LLMClient` with an `OpenRouterLLMClient` adapter that targets `https://openrouter.ai/api/v1/`. Same retry policy as the Anthropic adapter. Structured output uses OpenAI's function-calling shape (which OpenRouter exposes for all OpenAI-compatible models).

OpenRouter is selected via `LLM_PROVIDER=openrouter` env var in the composition layer. Default remains Anthropic.

## Consequences

**Easy:**
- Switching between Anthropic and OpenRouter is a one-line composition change.
- Different models can be tried per call via the `model=` parameter, including non-Anthropic models routed through OpenRouter.
- OpenRouter handles many providers behind one API key — useful for experimentation.

**Hard:**
- One more failure mode: OpenRouter is itself an availability dependency.
- Per-call cost reporting requires reading OpenRouter's response headers, not the underlying provider's. Minor friction.
- Some model-specific features (e.g., Anthropic's extended thinking, OpenAI's structured outputs) may not be exposed identically through OpenRouter.

**Forecloses:**
- Nothing — having an alternative is strictly additive. Removing it would be a deliberate decision.

## Alternatives considered

- **No alternative; commit fully to Anthropic** — rejected. Single-vendor risk is real; having a second adapter ready avoids panic during an Anthropic outage.
- **Use LiteLLM as a unifying proxy** — viable. LiteLLM is a similar idea (route to many providers). OpenRouter wins on operational simplicity (no self-hosted proxy needed). Reconsider LiteLLM if a self-hosted-inference-gateway requirement appears.

## Review trigger

- OpenRouter's reliability degrades to the point that it cannot serve as a credible fallback.
- A direct provider integration (e.g., OpenAI, Azure OpenAI) becomes valuable enough to add as its own adapter rather than going through OpenRouter.
