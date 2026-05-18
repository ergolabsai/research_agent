---
id: adapters-driven-0001
title: Anthropic as the default `LLMClient` adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The system needs a default LLM provider. The choice is part performance fit, part cost, part operational characteristics (rate limits, structured-output support, vision capability).

Anthropic Claude was selected for the prototype based on quality fit and reliability for the kind of analytical/structured tasks the validation pipeline performs.

## Decision

Implement `LLMClient` with an `AnthropicLLMClient` adapter that wraps `ChatAnthropic` from `langchain-anthropic`. Default model: `claude-haiku-4-5-20251001`. Configurable per-call via the `model=` parameter on the port.

Retries use `tenacity` (`stop_after_attempt(3)`, exponential backoff 1–10s) inside the adapter — callers do not configure retries.

Structured output uses LangChain's `with_structured_output(PydanticModel)`, which wraps Anthropic's tool-use under the hood.

Current implementation: `advisor_pipeline/llm.py` (will move to `adapters/driven/llm/anthropic.py`).

## Consequences

**Easy:**
- Quality is well-matched to the validation task; few prompt regressions across model versions in the Claude family.
- Vision support is native and works through the same client.
- API rate limits are generous for the prototype's scale.

**Hard:**
- Single-vendor dependency. Outage of Anthropic's API blocks all LLM-using paths.
- Cost is non-trivial at scale. The four-call figure-evaluator pattern compounds.

**Forecloses:**
- Default routing to other providers without a composition change.

## Alternatives considered

- **OpenAI (GPT family)** — viable; established. Anthropic was chosen on quality fit at lower cost for the validation task. Reconsidered if the cost/quality landscape shifts.
- **Local model (LLaMA, Mixtral) via vLLM or Ollama** — rejected as default. Quality gap is too large for the validation pipeline. Possible future as a low-cost path for cheap subtasks.
- **OpenRouter as the *default*** — rejected. OpenRouter is implemented as an *alternative* adapter ([0002](./0002-openrouter-llm-adapter.md)). Routing through it adds latency and a billing-relationship layer; direct Anthropic is preferred for production.

## Review trigger

- A model from another provider demonstrably matches Claude Haiku on the validation task at materially lower cost.
- Anthropic API instability becomes a recurring operational issue.
- Vendor-diversification becomes a procurement requirement (compliance, business continuity).
