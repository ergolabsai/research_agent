---
id: capabilities-validation-0005
title: Validation result is fully structured JSON, not embedded markdown
status: proposed
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

`ValidationResult.overall_assessment.review` is currently a single markdown string produced by the `compile_results` step. The frontend renders it via a markdown renderer for display. The structured fields the rest of the result contains (per-step evidence, figure evaluations, math evaluations, scored related papers) are not duplicated inside the markdown.

This works for display but blocks several future uses:

- Programmatic consumers (CLI, future connectors) must parse markdown to extract anything beyond the prose.
- Future UI variants (graph-only views, claim-level overlays) need direct access to per-section structure.
- The frontend already has a `GraphAnalysis` type that describes the structured shape — there is an existing target.

## Decision

The `compile_results` step produces a fully structured `ValidationResult` with no markdown-embedded fields. The current `overall_assessment.review` markdown becomes:

- `overall_assessment.summary` (short prose, 1–2 paragraphs).
- `overall_assessment.strengths` (list of structured items).
- `overall_assessment.weaknesses` (list of structured items, each referencing the relevant step or evaluation).
- `overall_assessment.recommendations` (list of structured items).

Markdown rendering becomes a *frontend* concern: the frontend assembles the prose from the structured fields for display. The contract emits no markdown.

The exact shape is defined by the existing `GraphAnalysis` TypeScript type in `frontend/src/types/index.ts` plus the structured-assessment additions above. The Pydantic contract in `core/contracts/validation.py` is the source of truth; the frontend type becomes generated from it (see [frontend/0004](../../../frontend/decisions/0004-generated-types-from-contracts.md)).

## Consequences

**Easy:**
- All consumers get structured data. The CLI can render `--json` without parsing markdown.
- Frontend rendering is fully under frontend control. A graph-view variant can present the same data differently.
- The contract becomes the schema of "what we know about a paper" — programmatically usable by future tooling.

**Hard:**
- The `compile_results` LLM prompt must produce structured output via `with_structured_output(OverallAssessment)`. This is what the rest of the pipeline already does — no new capability needed, but the prompt must be rewritten.
- Frontend display logic that currently renders one markdown blob must be expanded to render multiple structured sections. This is a clear refactor with a known target.
- Existing job records carry the markdown-form `overall_assessment.review`. A migration step is needed (either a one-shot reformat via LLM, or a "legacy field" fallback in the contract during a transition window).

**Forecloses:**
- "Just shove a markdown blob into the response" as a future shortcut. The contract is the system's spoken language; it stays structured.

## Alternatives considered

- **Keep markdown; add structured fields alongside** — rejected. Duplicates information, leaves ambiguity about which is canonical, and lets the markdown drift from the structured fields over time.
- **Structured fields only on the API; markdown only on the CLI** — rejected. Two contracts for the same data is worse than one. The CLI's `--json` mode demands structured.
- **Server-side markdown rendering from structured fields** — rejected as default. Rendering belongs in the consumer. The CLI may want plain text; the frontend wants HTML; a connector may want its own format.

## Review trigger

- A genuine use case for a single canonical prose form arrives (e.g., emailing a summary). At that point introduce a *separate* `render_summary_markdown` use-case that takes a structured `ValidationResult` and produces markdown — but the contract itself stays structured.
