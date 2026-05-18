# Pipeline Sequence — Submit → Poll → Render

End-to-end interaction for the primary user flow: a user submits a paper and watches the validation pipeline run.

```mermaid
---
config:
  theme: neo-dark
  look: neo
---
sequenceDiagram
    actor User
    participant FE as Frontend<br/>(AgentPanel)
    participant API as FastAPI<br/>(pipeline.py)
    participant Svc as PipelineService
    participant DB as SQLite<br/>(PipelineJob, StepLog)
    participant Orch as Orchestrator<br/>(thread pool)
    participant Agents as Agents<br/>(Librarian/Figure/Math)
    participant MCP as Calculator MCP
    participant LLM as Anthropic
    participant Lance as LanceDB
    participant SS as Semantic Scholar

    User->>FE: Click "Validate"
    FE->>API: POST /api/pipeline/validate<br/>{paper_text, figures, bibliography}
    API->>Svc: create_job(...)
    Svc->>DB: INSERT PipelineJob<br/>status=pending
    DB-->>Svc: job_id
    Svc->>Orch: BackgroundTasks: run_pipeline_async(job_id)
    API-->>FE: { job_id }

    par Polling loop
        loop every 2s
            FE->>API: GET /api/pipeline/status/:job_id
            API->>DB: SELECT PipelineJob
            DB-->>API: { status, current_step, step_name }
            API-->>FE: progress
        end
    and Pipeline execution
        Orch->>DB: UPDATE status=running

        Note over Orch,LLM: Node 1 — make_context
        Orch->>LLM: invoke_text(CONTEXT_MAKER)
        LLM-->>Orch: paper_context
        Orch->>DB: INSERT StepLog #1

        Note over Orch,Lance: Node 2 — gather_papers (Librarian pass 1)
        Orch->>Agents: Librarian.gather_papers()
        Agents->>Lance: FTS(cited_titles) + vector(related)
        Lance-->>Agents: papers
        Agents->>SS: fallback for missing citations
        SS-->>Agents: abstracts
        Agents-->>Orch: LibrarianResult
        Orch->>DB: INSERT StepLog #2

        Note over Orch,LLM: Node 3 — map_logic
        Orch->>LLM: get_structured_output(PaperStructure)
        LLM-->>Orch: paper_structure
        Orch->>DB: INSERT StepLog #3

        Note over Orch,LLM: Node 4 — find_evidence
        Orch->>LLM: get_structured_output(StepEvidence[])
        LLM-->>Orch: step_evidence
        Orch->>Orch: build_paper_graph()
        Orch->>DB: INSERT StepLog #4

        Note over Orch,LLM: Node 5 — evaluate_figures
        loop per figure
            Orch->>Agents: FigureEvaluator.run(figure)
            Agents->>LLM: invoke_vision × 4
            LLM-->>Agents: descriptions + assessments
        end
        Agents-->>Orch: figure_evaluations
        Orch->>DB: INSERT StepLog #5

        Note over Orch,MCP: Node 6 — evaluate_math
        Orch->>Agents: MathEvaluator(mcp_client).run()
        loop per equation
            Agents->>MCP: calculate/verify/list_formulas
            MCP-->>Agents: result
            Agents->>LLM: reasoning step
        end
        Agents-->>Orch: math_evaluations
        Orch->>DB: INSERT StepLog #6

        Note over Orch,LLM: Node 7 — score_papers (Librarian pass 2)
        loop per related paper
            Orch->>LLM: score relevancy + convergence
        end
        Orch->>DB: INSERT StepLog #7

        Note over Orch,LLM: Node 8 — compile_results
        Orch->>LLM: get_structured_output(OverAllReview)
        LLM-->>Orch: validation_result
        Orch->>DB: UPDATE PipelineJob<br/>status=completed,<br/>result_json, graph_json
    end

    FE->>API: GET /api/pipeline/results/:job_id
    API->>DB: SELECT result_json
    DB-->>API: ValidationResult
    API-->>FE: review + step_validations

    FE->>API: GET /api/pipeline/graph/:job_id
    API-->>FE: NetworkX node-link JSON

    FE->>API: GET /api/pipeline/analysis/:job_id
    API->>Svc: get_graph_analysis()
    Svc->>DB: SELECT graph_json
    Svc->>Svc: NetworkX queries<br/>(contradictions, invalid math,<br/>librarian stats)
    Svc-->>API: GraphAnalysis
    API-->>FE: analysis

    FE->>User: Render tabs:<br/>Validate / Graph / Results
```

## Notes on the flow

- **Polling, not streaming.** The frontend hits `/status/:jobId` every 2s. Candidate for SSE or WebSocket upgrade — the pipeline already has a step callback that could emit events.
- **Pipeline is serial.** Every node waits on the previous. Figures and math could parallelize trivially; related-paper scoring could batch.
- **Durability gap.** `BackgroundTasks` runs in the same process. If uvicorn restarts mid-pipeline, the job is stuck in `running`. A real queue (Arq / RQ / Celery) with a retry/claim model would fix this.
- **Three separate fetches at the end** (`results`, `graph`, `analysis`). Each hits the DB and deserializes `graph_json`. A single `/complete/:jobId` endpoint or GraphQL-style selector could cut a round-trip and decode cost.

## Failure modes — what happens when...

| Failure                              | Current behavior                                                 | What probably should happen                      |
| ------------------------------------ | ---------------------------------------------------------------- | ------------------------------------------------ |
| Anthropic call fails                 | `@retry` 3× exp backoff; exception → job `failed` with stack     | Good; consider a circuit breaker for outages     |
| MCP calculator unreachable           | Tool call raises; `@retry` doesn't cover it → step fails         | Graceful fallback: mark math `is_valid=None`      |
| Process restart mid-run              | Job stuck at `running` forever                                   | Durable queue + claim/ack or startup sweeper     |
| LanceDB missing / empty              | Librarian returns no related papers silently                     | Assert at startup; warn in status                |
| Figures exceed vision context        | Vision call truncates or errors                                  | Pre-flight size check, downscale before upload   |
| User navigates away during polling   | No harm — backend keeps running; user can come back              | Fine as long as we don't silently drop websocket |

## Questions for the architect

- Is 2-second polling the right cadence, or should we push SSE updates?
- Should failed jobs be auto-retriable from the UI, or always manual?
- Should we cap pipeline runtime (e.g., 10 minutes) and kill with a clear error, or leave it unbounded?
