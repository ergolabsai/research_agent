# Research Advisor

Multi-agent system that validates scientific research papers. Users paste paper text, and the system analyzes logical structure, verifies math, finds related papers via LanceDB and Semantic Scholar, evaluates figures, and produces a confidence-scored assessment.

## Project Structure

| Module              | Stack                                 | Purpose                                                               |
| ------------------- | ------------------------------------- | --------------------------------------------------------------------- |
| `frontend/`         | React 18 + TypeScript + MUI v5 + Vite | SPA with auth, document/workspace management, and paper validation UI |
| `backend/`          | FastAPI + SQLModel + SQLite           | REST API server: auth, CRUD, and async pipeline job runner            |
| `advisor_pipeline/` | LangGraph + LangChain + Anthropic + MCP | 8-step validation pipeline with specialized agents                  |

## How They Connect

```
Frontend (localhost:4174)  --Vite proxy /api-->  Backend (localhost:8070)  --ThreadPool-->  advisor_pipeline
```

1. Frontend submits paper text via `AgentPanel`, calling `POST /api/pipeline/validate`
2. Backend creates a `PipelineJob` in SQLite and spawns `AdvisorOrchestrator.run()` in a thread pool
3. Frontend polls `GET /api/pipeline/status/:jobId` every 2s for progress
4. Pipeline runs 8 LangGraph nodes; after each, callback persists output to `PipelineStepLog`
5. On completion, results and graph JSON are saved to the `PipelineJob` row
6. Additional endpoints: graph (`/graph/:jobId`), figures (`/figures/:jobId`), analysis (`/analysis/:jobId`), per-step logs (`/steps/:jobId`)

## Development

### Starting the app

```bash
# One command (Windows):
.\scripts\start-dev.bat
# Starts backend on :8070, then frontend on :4174

# Manual start:
.\backend\.venv\api\Scripts\python.exe -m uvicorn app.main:app --reload --port 8070 --app-dir backend
cd frontend && npm run dev
```

### Frontend-only mock mode

```bash
cd frontend && npm run dev:mock
# Or: make mock
```

### Python environment

- Python 3.12, venv at `backend/.venv/api/`
- Backend deps: `backend/requirements.txt`
- Pipeline deps: `pyproject.toml` (installed as editable package)

### Docker

- `make dev` — CPU dev mode with hot-reload
- `make dev-gpu` — GPU dev mode
- `make up-cpu` / `make up` — production CPU / GPU
- See `makefile` for 60+ targets

## Key Conventions

- All timestamps use `America/Los_Angeles` timezone (`backend/app/time.py`)
- Backend sessions use SQLModel's `Session` generator dependency (`get_session()`)
- Frontend uses Axios with automatic token refresh — never manually handle 401s
- Pipeline agents use `@retry` (3 attempts, exponential backoff) for all LLM calls
- Structured LLM output uses `ChatAnthropic.with_structured_output(PydanticModel)` — not instructor
- Python linting: Ruff (line length 100, target py311)
- Frontend linting: ESLint with React hooks plugin

## Frontend Details

- **Build**: Vite on port 4174, proxies `/api` to `http://localhost:8070` (configurable via `API_PROXY_TARGET` env)
- **Routing** (react-router-dom v6):
  - `/` — LandingPage (public)
  - `/auth/login`, `/auth/register` — auth forms
  - `/app/dashboard` — documents + workspaces grid
  - `/app/editor/:id` — editor with auto-save, attachments, validation panel
- **Auth**: JWT access token in memory + refresh token as HTTP-only cookie. `AuthProvider`/`useAuth` context. Axios interceptors handle 401 refresh.
- **State**: React Context (auth, dialogs, theme) + page-level `useState`. No external state library in active use.
- **API client** (`src/api/client.ts`): Axios at `/api` base. Modules: `authAPI`, `documentsAPI`, `workspacesAPI`, `usersAPI`, `pipelineAPI`. Pipeline includes `analysis()` for graph analysis data.
- **Mock mode**: `npm run dev:mock` — Vite mock mode with axios interception from `src/mocks/mockApi.ts`, configurable via `src/mocks/agentConfig.ts`. Mock fixtures use real validation data from the "Ultrafast isomerization" paper. Graph analysis fixture is in `src/mocks/graphAnalysisFixture.ts`.
- **Theming**: 6 MUI themes (3 light, 3 dark), persisted in localStorage. Theme palette includes a `discrete` color array for graph/data-viz UI.
- **Editor**: MUI TextField-based editor in `EditorPage.tsx` (Draft.js and KaTeX are installed but not currently wired up).
- **Markdown rendering**: `react-markdown` + `remark-gfm` via `MarkdownRenderer` component (`src/components/MarkdownRenderer.tsx`). Used in the Validate tab to render the overall review.
- **Graph visualization**: `react-force-graph-2d` in `src/components/GraphContent.tsx` for the paper graph view.
- **Math rendering**: KaTeX via `src/utils/katexRenderer.ts` (used by `RichView` and `AgentPanel`).
- **Key components**: `Sidebar`, `AgentPanel`, `GraphContent`, `MarkdownRenderer`, `DocumentItem`, `WorkspaceItem`, `SettingsMenu`.
- **Validate tab UI**: On completion, shows two MUI Accordion sections: "Validation Results" (markdown-rendered overall review, default expanded) and "Graph Analysis" (node counts, steps without evaluations, contradicted steps as nested accordions). Data comes from separate API calls: `pipelineAPI.results()` for the review, `pipelineAPI.analysis()` for graph analysis.

## Backend Details

- **Entry**: `backend/app/main.py` — CORS (fully open), SQLite auto-creation, static attachment serving at `/static/attachments`.
- **DB**: SQLite via SQLModel. Models: `User`, `Document`, `DocumentShare`, `Attachment`, `Workspace`, `WorkspaceMember`, `PipelineJob`, `PipelineStepLog`.
- **Auth** (`security.py`): HS256 JWT. Access = 15min, refresh = 7 days (HTTP-only cookie with rotation). Passwords: bcrypt. Guest: `POST /auth/try`.
- **Storage** (`storage.py`): `local` (filesystem) or `minio` (S3-compatible), controlled by `STORAGE_BACKEND` env var.
- **Routes**: `auth.py`, `documents.py`, `workspaces.py`, `users.py`, `pipeline.py`
- **Pipeline service** (`services/pipeline_service.py`): SQLite job store. Runs orchestrator in thread pool. Hydrates figure refs from storage. Builds NetworkX DiGraph with analysis helpers after completion.

## Advisor Pipeline Details

### Orchestrator (`orchestrator.py`)

LangGraph `StateGraph` with 8 sequential nodes:

```
START → make_context → gather_papers → map_logic → find_evidence → evaluate_figures → evaluate_math → score_papers → compile_results → END
```

State flows through `AdvisorState` TypedDict. Optional `on_step_complete` callback for progress tracking.

### LLM Client (`llm.py`)

Single shared `ChatAnthropic` instance (default: `claude-haiku-4-5-20251001`). Also supports OpenRouter. Three helpers with `@retry`: `get_structured_output`, `invoke_vision`, `invoke_text`.

### Agents

| Agent             | Type                        | Purpose                                                                    |
| ----------------- | --------------------------- | -------------------------------------------------------------------------- |
| `FigureEvaluator` | Direct LLM (4 calls/figure) | Vision describes submitted figure → compare with predicted/expected → assess claims |
| `MathEvaluator`   | LangGraph ReAct agent       | MCP calculator tools to verify equations (±500 char context extraction)    |
| `Librarian`       | Two-pass LLM agent          | Pass 1: gather papers (LanceDB + Semantic Scholar). Pass 2: score relevancy + convergence. |

### MCP Servers

**Advisor Server** (`mcp_servers/advisor_server/`) — stdio:
- 12 prompt templates, 5 tools (`load_paper`, `search_semantic_scholar`, `get_paper_abstract`, `check_paper_accessibility`, `extract_doi`)

**Calculator Server** (`mcp_servers/calculator_server/`) — HTTP/SSE or stdio:
- 4 tools (`calculate`, `verify`, `list_formulas`, `describe_formula`)
- SQLite formula table + SymPy solver, includes `ml_validation` formulas

### MCP Client (`mcp_client.py`)

`CalculatorClient` — sync wrapper around async MCP SDK. Runs asyncio loop in a daemon thread to avoid conflicts with LangGraph's sync execution.

### Data Models (`models/schemas.py`)

Key types: `PaperStructure`, `Evidence`, `StepEvidence`, `FigureEvaluation`, `MathEvaluation`, `RelatedPaper`, `LibrarianResult`, `ValidationResult` (final output with confidence score).

### Paper Graph (`models/paper_graph.py`)

NetworkX `DiGraph` with typed nodes and edges. Built incrementally during pipeline. Query helpers: `get_contradicted_steps`, `get_invalid_math`, `get_librarian_statistics`, `get_figure_confirmation_counts`, etc.

## Configuration (`advisor_pipeline/config/settings.py`)

Pydantic `BaseSettings` from `.env`. Key groups: API keys, LLM (provider/model/temperature/max_tokens), DB, LanceDB, MCP, storage (local/minio), auth.

## Data Stores

| Store   | Technology            | Used for                                                         |
| ------- | --------------------- | ---------------------------------------------------------------- |
| SQLite  | SQLModel (SQLAlchemy) | Users, documents, workspaces, attachments, pipeline jobs/steps, calculator formulas |
| LanceDB | lancedb + embeddings  | arXiv paper search (vector + full-text) for Librarian agent      |

## Known Issues

- CORS is fully open (`allow_origins=["*"]`) — tighten for production
- `users/search` endpoint has no auth requirement
- Dead dependencies in package.json: `draft-js`, `react-draft-wysiwyg`, `zustand` (installed but not imported). `katex` IS used in `src/utils/katexRenderer.ts`.
- `instructor` in `requirements.txt` but unused (structured output uses `with_structured_output()`)

## TODO

- **Backend structured validation output**: The `compile_results` pipeline step currently produces `ValidationResult` with `overall_assessment.review` as a single markdown string. The backend should be updated to return structured JSON (with the review already parsed into sections) so the frontend doesn't depend on markdown formatting. The frontend `GraphAnalysis` type (`src/types/index.ts`) and the mock fixture (`src/mocks/graphAnalysisFixture.ts`) define the expected shape — the backend `/pipeline/analysis/:jobId` endpoint should return data matching this interface. The mock currently serves `validation_results.md` content converted to JSON fixtures; once the backend emits proper JSON, the mock fixtures should be updated to match.
