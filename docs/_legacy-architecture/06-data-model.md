# Data Model

Entity-relationship view of everything persisted to SQLite, plus the "shape" data stored in LanceDB and object storage.

## SQLite entities (`backend/data/app.db`)

```mermaid
---
config:
  theme: neo-dark
  look: neo
---
erDiagram
    User {
        int id PK
        string email UK
        string username UK
        string hashed_password
        datetime created_at
        datetime updated_at
    }
    Document {
        int id PK
        string title
        text content
        int owner_id FK
        int workspace_id FK "nullable"
        datetime created_at
        datetime updated_at
    }
    DocumentShare {
        int id PK
        int document_id FK
        int shared_with_user_id FK
        string permission
        datetime shared_at
    }
    Attachment {
        int id PK
        int document_id FK
        string filename
        string object_key
        string content_type
        int size
        datetime created_at
    }
    Workspace {
        int id PK
        string name
        int owner_id FK
        datetime created_at
        datetime updated_at
    }
    WorkspaceMember {
        int id PK
        int workspace_id FK
        int user_id FK
        string role
        datetime added_at
    }
    PipelineJob {
        int id PK
        string job_id UK
        int user_id FK
        string paper_id
        string title
        string status "pending|running|completed|failed"
        int current_step
        int total_steps
        string step_name
        text error
        text paper_text
        json bibliography_json
        json figures_json
        json result_json
        json graph_json
        datetime created_at
        datetime completed_at
    }
    PipelineStepLog {
        int id PK
        string job_id FK
        string step_name
        int step_number
        string status
        json output
        json prompts
        float duration_seconds
        datetime started_at
        datetime completed_at
    }

    User ||--o{ Document : owns
    User ||--o{ Workspace : owns
    User ||--o{ PipelineJob : submits
    User ||--o{ WorkspaceMember : joins
    User ||--o{ DocumentShare : receives
    Workspace ||--o{ WorkspaceMember : has
    Workspace ||--o{ Document : contains
    Document ||--o{ Attachment : has
    Document ||--o{ DocumentShare : shared_via
    Document ||--o{ PipelineJob : validates
    PipelineJob ||--o{ PipelineStepLog : logs
```

## Key design choices

- **`PipelineJob` stores inputs *and* outputs.** `paper_text`, `bibliography_json`, `figures_json` are the inputs snapshot; `result_json` and `graph_json` are the outputs. This means a job is fully reconstructable from its row — nice for reruns and debugging.
- **`PipelineStepLog` per node.** `output` is the state delta returned by the node; `prompts` captures what was sent to the LLM. This is the audit trail.
- **`graph_json`** is NetworkX node-link format. The backend rebuilds the `DiGraph` on demand for analysis queries.
- **`figures_json`** is `{figure_name: {base64, media_type, predicted?}}` — figures are inlined as base64, not object-storage refs, inside the job row. Object storage is used for the *original* attachments on `Document`; the pipeline gets a materialized copy.

## Pipeline-side models (Pydantic — not persisted directly, serialized into `result_json`)

Source: [advisor_pipeline/models/schemas.py](../../advisor_pipeline/models/schemas.py).

```mermaid
---
config:
  theme: neo-dark
  look: neo
---
classDiagram
    class ValidationResult {
        +PaperStructure paper_structure
        +list~StepValidation~ step_validations
        +OverAllReview overall_assessment
        +float confidence_score
    }
    class PaperStructure {
        +list~LogicalStep~ steps
        +string abstract
    }
    class LogicalStep {
        +int number
        +string description
        +list~string~ claims
        +list~int~ depends_on
    }
    class StepEvidence {
        +int step_number
        +list~Evidence~ evidence
    }
    class Evidence {
        +string type "figure|math|citation"
        +string location
        +string content
    }
    class FigureEvaluation {
        +string figure_name
        +string actual_description
        +string expected_description
        +string comparison
        +list~ClaimAssessment~ claim_assessments
    }
    class MathEvaluation {
        +string equation
        +bool is_valid
        +string notes
        +list~string~ trace
    }
    class RelatedPaper {
        +string id
        +string title
        +string source "lancedb|semantic_scholar"
    }
    class RelatedPaperScored {
        +float relevancy
        +float convergence
    }
    class LibrarianResult {
        +list~RelatedPaper~ cited
        +list~RelatedPaper~ related
    }

    ValidationResult --> PaperStructure
    PaperStructure --> LogicalStep
    ValidationResult --> StepEvidence
    StepEvidence --> Evidence
    ValidationResult --> FigureEvaluation
    ValidationResult --> MathEvaluation
    RelatedPaperScored --|> RelatedPaper
    LibrarianResult --> RelatedPaper
```

## Other data stores

| Store                | Shape                                                                 | Purpose                                          |
| -------------------- | --------------------------------------------------------------------- | ------------------------------------------------ |
| LanceDB `arxiv_lancedb/` | arXiv papers with vector embeddings (`BAAI/bge-small-en-v1.5`) + FTS | Related-paper search for the Librarian          |
| Formula DB (SQLite)  | `Formula(id, name, latex, variables, category)`                       | Calculator MCP — SymPy-solvable formulas         |
| Object storage       | `object_key → bytes`                                                  | Figures + attachments (local FS or MinIO)        |

## Known issues

- **`figures_json` as base64 inside the job row** balloons SQLite rows. For larger papers / batching, store refs to object storage instead.
- **No migrations.** `SQLModel.metadata.create_all()` at startup creates missing tables but doesn't evolve existing ones. Will need Alembic before launch if the schema changes after users have data.
- **No soft delete / audit columns** on most tables — deletes are hard. Fine for now; add `deleted_at` when we have shared documents people can't afford to lose.

## Questions for the architect

- SQLite → Postgres timing. When does the single-writer bottleneck start to hurt?
- Should `PipelineStepLog.output` be capped / truncated? It holds whole state deltas and can be large.
- Do we want event sourcing for jobs (append-only log of state transitions) or is the current "update the row" model enough?
