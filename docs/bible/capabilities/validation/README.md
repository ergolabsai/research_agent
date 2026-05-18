# Capability: Validation

Validation is the system's primary capability. A user submits a scientific paper — its text, figures, and bibliography — and receives back a structured assessment: how confident is the system in the paper's claims, where are the weak steps, what does related work say, and is the math sound?

This capability is the "AI half" of the application. The other half — [collaboration](../collaboration/) — is what gets the paper in front of the validation pipeline in the first place.

## Concepts

- **Paper** — a submitted scientific document. Carries text, optional figures, optional bibliography, and metadata.
- **Logical step** — one claim or argument in the paper's main thread. The validation pipeline maps a paper into a sequence of logical steps before reasoning about evidence for each one.
- **Evidence** — a citation, an internal figure, or a piece of math that supports (or contradicts) a logical step.
- **Figure evaluation** — an assessment of a figure: what it shows, whether it matches a predicted/expected figure, and which claims it confirms or contradicts.
- **Math evaluation** — verification of an equation referenced in the paper. Uses a calculator port to check correctness.
- **Related paper** — a paper from the knowledge base (currently arXiv) that the validation deems relevant. Carries a relevancy score and a convergence score (does it agree with the submitted paper?).
- **Validation result** — the final structured output: confidence score, per-step evidence, figure/math evaluations, scored related papers, overall assessment.
- **Paper graph** — a typed graph (nodes: papers, steps, evidence, figures, math, related papers; edges: supports/contradicts/cites). Built incrementally during validation; queryable after the fact for analyses like "which steps lack any evaluation?" or "which figures contradict their claims?"

## Use-cases this capability exposes

(Once migration is complete, each lives as a file under `core/use_cases/validation/`.)

- `ValidatePaper` — run the full validation pipeline against a paper.
- `GetJob` — fetch a validation job by id.
- `ListJobs` — list jobs for a principal.
- `GetGraphAnalysis` — return graph-derived summaries (contradictions, invalid math, related papers) for a completed job.
- `GetStepLogs` — fetch per-step output for a job (used for transparency).
- `ReplayJob` *(dev/admin)* — rerun a completed job, optionally with adjusted parameters.

## Pipeline shape (orchestration)

The validation pipeline is currently an **8-step linear sequence**, expressed as a LangGraph state graph:

```
make_context → gather_papers → map_logic → find_evidence → evaluate_figures → evaluate_math → score_papers → compile_results
```

Each step produces structured state that the next step consumes. The orchestrator is a core service ([architecture/0003](../../architecture/decisions/0003-core-has-no-io.md)); the work each step performs goes through driven ports (LLM, paper index, calculator, object storage).

See [decisions/0001-eight-step-linear-graph](./decisions/0001-eight-step-linear-graph.md) for the choice of sequence and why parallelism is deferred.

## Sub-agents

The orchestrator coordinates three specialized agents that live as core services:

- **`FigureEvaluator`** — vision-based assessment. For each figure, makes ~4 LLM calls (describe submitted, describe predicted, compare, assess claims) and emits a `FigureEvaluation`. See [decisions/0003-figure-eval-4-calls](./decisions/0003-figure-eval-4-calls.md).
- **`MathEvaluator`** — a LangGraph ReAct agent that uses a `Calculator` port to verify equations. Extracts ±500 characters of context around each equation reference before reasoning about it.
- **`Librarian`** — two-pass agent. Pass 1: gather related papers (search `PaperIndex` + Semantic Scholar). Pass 2: score each related paper for relevancy and convergence.

## Ports this capability depends on

- [`LLMClient`](../../ports/decisions/0001-llm-client-port.md) — text and vision LLM calls.
- [`PaperIndex`](../../ports/decisions/0002-paper-index-port.md) — search the local paper corpus.
- [`Calculator`](../../ports/decisions/0003-calculator-port.md) — verify equations.
- [`JobStore`](../../ports/decisions/0004-job-store-port.md) — persist job state and results.
- [`ObjectStorage`](../../ports/decisions/0005-object-storage-port.md) — fetch submitted figure bytes.
- [`Clock`](../../ports/decisions/0008-clock-port.md) — timestamps on jobs and step logs.

## ADRs in this capability

| # | Title | Status |
|---|---|---|
| [0001](./decisions/0001-eight-step-linear-graph.md) | Eight-step linear pipeline | accepted |
| [0002](./decisions/0002-langgraph-in-core.md) | LangGraph allowed in core | accepted |
| [0003](./decisions/0003-figure-eval-4-calls.md) | Four LLM calls per figure | accepted |
| [0004](./decisions/0004-paper-graph-as-domain.md) | Paper graph as a domain entity | accepted |
| [0005](./decisions/0005-validation-result-contract.md) | Validation result shape (structured, not markdown) | proposed |
