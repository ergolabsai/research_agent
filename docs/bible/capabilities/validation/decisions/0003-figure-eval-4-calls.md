---
id: capabilities-validation-0003
title: Four LLM calls per figure in `FigureEvaluator`
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

`FigureEvaluator` is the most expensive sub-agent per artifact: each figure requires multiple vision calls. The question is whether to keep the four-call structure (describe submitted → describe predicted → compare → assess claims) or fuse them into a single multi-modal prompt.

Cost, latency, and quality all push in different directions.

## Decision

`FigureEvaluator` performs **four LLM calls per figure**:

1. Vision-describe the *submitted* figure (what does this image actually show?).
2. Vision-describe the *predicted/expected* figure if one is provided (what should it have shown?).
3. Compare the two descriptions textually.
4. Assess which claims the figure confirms or contradicts.

Each call is structured-output via the `LLMClient` port. The orchestrator does not know how many calls happen — it asks for one `FigureEvaluation`.

## Consequences

**Easy:**
- Each call has a single, optimizable prompt. Quality regressions are localized.
- Intermediate outputs are inspectable (the per-figure description text is useful in the step log for transparency).
- Vision and text models can be different (vision for steps 1–2, text for 3–4). The port allows it.

**Hard:**
- Four times the LLM cost per figure. With many figures, this dominates job cost.
- Four times the latency unless calls are parallelized within the agent (currently serial).
- More retry exposure: each of the four calls can fail and trigger the `@retry` wrapper.

**Forecloses:**
- A "describe and assess in one shot" approach unless explicitly proven equivalent in quality. The current decomposition is what makes the assessment trustworthy.

## Alternatives considered

- **Single fused prompt** ("here is the submitted figure, the predicted figure, and the claims — return a structured FigureEvaluation") — viable on a sufficiently capable model. Was not chosen because (a) early experiments showed worse claim-confirmation accuracy when fused, and (b) the four-step decomposition gives better step-log transparency.
- **Three calls (skip predicted description)** — viable when no predicted figure is provided. The current implementation already short-circuits step 2 when there is no predicted figure; this is the same idea framed as a structural decision.
- **Parallelize the four calls within the agent** — deferred. Would halve per-figure latency. Worth doing once latency dominates cost. Not now.

## Review trigger

- A new vision model demonstrably matches the four-call quality with one fused call.
- Per-figure cost becomes the largest single line on the API bill, and the four-call structure is the binding constraint.
- A common failure mode emerges that suggests one of the four calls is consistently weak — that call gets prompt-engineered or split further, but the overall structure may remain.
