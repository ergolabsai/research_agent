# Research Advisor

A multi-agent system that validates scientific research papers. Paste in a paper, and the system analyzes its logical structure, verifies math, finds related papers via LanceDB and Semantic Scholar, evaluates figures, and produces a confidence-scored assessment.

Built with a LangGraph orchestrator, MCP tool servers, and structured LLM output via `ChatAnthropic.with_structured_output()`.

## Architecture

```
Frontend (localhost:5173)       Backend (localhost:8070)        Pipeline (LangGraph)
========================        =====================          ====================
ValidatePage                    POST /api/pipeline/validate    1. Make Context
  - paste paper text     --->     creates PipelineJob          2. Gather Papers (pass 1)
  - polls every 2s       <---   GET  /api/pipeline/status/:id  3. Map Logic
  - step-by-step results        GET  /api/pipeline/results/:id 4. Find Evidence
                                                               5. Evaluate Figures
DashboardPage                   /api/documents/*               6. Evaluate Math
EditorPage                      /api/workspaces/*              7. Score Papers (pass 2)
Login / Register                /api/auth/*                    8. Compile Results
```

The Vite dev server proxies `/api` requests to the FastAPI backend. The backend runs the pipeline in a thread pool via `loop.run_in_executor` and exposes progress via polling endpoints.

**Data stores:**

- **SQLite** (via SQLModel) — users, documents, workspaces, attachments, shares, pipeline jobs + step logs, calculator formulas
- **LanceDB** — arXiv paper embeddings for vector + full-text search (used by Librarian agent and migration scripts)
- **In-memory dicts** — pipeline job tracking (not persistent across restarts)

## Project Structure

```
.
├── advisor_pipeline/           # LangGraph validation pipeline
│   ├── orchestrator.py         # StateGraph: 8 sequential nodes (two-pass Librarian design)
│   ├── llm.py                  # Shared ChatAnthropic + helpers (structured output, vision, text)
│   ├── mcp_client.py           # Sync wrapper for async MCP SDK (CalculatorClient)
│   ├── agents/
│   │   ├── figure_evaluator.py # 4-stage vision+text LLM evaluation per figure
│   │   ├── math_evaluator.py   # ReAct agent with MCP calculator tools
│   │   └── librarian.py        # Two-pass agent: gather papers (LanceDB FTS/vector + S2 fallback), then score relevancy/convergence
│   ├── mcp_servers/
│   │   ├── advisor_server/     # Stdio MCP server: 12 prompt templates + 5 tools
│   │   │   ├── server.py
│   │   │   ├── prompts.py      # All prompt templates (logic_mapper, evidence_finder, librarian_*, etc.)
│   │   │   └── tools.py        # load_paper, search_semantic_scholar, get_paper_abstract, etc.
│   │   └── calculator_server/  # HTTP/SSE + stdio MCP server: 4 math tools
│   │       ├── server.py       # SSE transport
│   │       ├── server_stdio.py # Stdio transport
│   │       └── tools/          # SQLite formulas + SymPy solver
│   ├── models/
│   │   ├── schemas.py          # Pydantic models (PaperStructure, Evidence, ValidationResult, etc.)
│   │   └── paper_graph.py      # NetworkX DiGraph with typed nodes/edges + query helpers
│   ├── config/
│   │   └── settings.py         # Pydantic BaseSettings from .env
│   └── utils/
│       ├── load_paper.py       # Load .tex + images + bibliography
│       ├── lancedb_search.py   # Shared LanceDB utility (vector + FTS search, lazy connections)
│       └── graph_visualizer.py # Pyvis interactive HTML visualization
│
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # App entry, CORS, lifespan (storage init), routers
│   │   ├── models.py           # SQLModel: User, Document, DocumentShare, Attachment, Workspace, WorkspaceMember
│   │   ├── security.py         # JWT HS256 auth, bcrypt, refresh token cookie rotation
│   │   ├── storage.py          # Dual-mode: local filesystem or MinIO (S3-compatible)
│   │   ├── time.py             # America/Los_Angeles timezone helper
│   │   ├── routes/
│   │   │   ├── auth.py         # Register, login, guest trial, refresh, me, logout
│   │   │   ├── documents.py    # CRUD, sharing, attachments (upload/download/delete)
│   │   │   ├── workspaces.py   # CRUD, members, document listing
│   │   │   ├── users.py        # Search by email/username
│   │   │   └── pipeline.py     # Submit validation, poll status, get results/graph/analysis
│   │   └── services/
│   │       └── pipeline_service.py  # In-memory job store, thread pool executor, graph builder
│   ├── data/                   # SQLite DB, LanceDB, attachments
│   └── scripts/                # LanceDB migration + navigator (Streamlit)
│
├── frontend/                   # React 18 + TypeScript + MUI v5
│   ├── vite.config.ts          # Dev server :5173, proxy /api → :8070
│   └── src/
│       ├── App.tsx             # Routes: /, /auth/*, /app/* (protected)
│       ├── api/client.ts       # Axios with auto token refresh, API modules
│       ├── pages/
│       │   ├── LandingPage.tsx # Public splash ("Ergo Labs: Advisor"), guest trial
│       │   ├── LoginPage.tsx   # Email/username + password
│       │   ├── RegisterPage.tsx
│       │   ├── MainPage.tsx    # App shell: sidebar + appbar + dialogs
│       │   ├── DashboardPage.tsx # Documents + workspaces grid, drag-and-drop
│       │   ├── EditorPage.tsx  # Title + content editor, auto-save, attachments
│       │   └── ValidatePage.tsx # Paste paper → submit → poll → results with confidence score
│       ├── components/         # Sidebar, DocumentItem, WorkspaceItem, SettingsMenu
│       ├── context/AuthContext.tsx  # JWT in memory + refresh cookie
│       ├── theme/              # 6 MUI themes (3 light, 3 dark), persisted in localStorage
│       └── types/index.ts      # Domain + pipeline TypeScript interfaces
│
├── scripts/
│   ├── start-dev.bat           # One-command startup (backend :8070 + frontend :5173)
│   └── setup-dev.bat           # Creates venv, installs deps
├── pyproject.toml              # Pipeline Python dependencies (editable install)
└── .github/
    └── copilot-instructions.md # Copilot Chat context file
```

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
# Change SECRET_KEY to something random
```

### 2. Python dependencies

```bash
# Windows (uses the setup script):
.\scripts\setup-dev.bat

# Manual:
cd backend
py -3.12 -m venv .venv/api
.venv/api/Scripts/activate     # or source .venv/api/bin/activate on Linux/Mac
pip install -r requirements.txt
cd ..
pip install -e .               # installs advisor_pipeline as editable package
```

### 3. Frontend dependencies

```bash
cd frontend
npm install
```

### 4. Run

```bash
# One command (Windows):
.\scripts\start-dev.bat

# Or manually in two terminals:

# Terminal 1: Backend
.\backend\.venv\api\Scripts\python.exe -m uvicorn app.main:app --reload --port 8070 --app-dir backend

# Terminal 2: Frontend
cd frontend && npm run dev
```

The frontend runs at `http://localhost:5173` and proxies `/api` calls to the backend at `http://localhost:8070`.

## How Validation Works

The pipeline is a LangGraph `StateGraph` with 8 sequential nodes. When you submit a paper through the Validate page or API:

1. **Make Context** — LLM enriches the paper text with relevant research context
2. **Gather Papers** _(Librarian pass 1)_ — `Librarian` finds related papers: extracts cited paper titles from the bibliography, searches LanceDB via FTS (falling back to Semantic Scholar), then uses LLM-crafted vector search queries to discover additional related work. Produces a context summary that enriches downstream analysis.
3. **Map Logic** — Extracts the paper's title, main claim, and ordered logical steps with dependencies (`PaperStructure`)
4. **Find Evidence** — For each logical step, finds supporting figures, equations, and citations (`StepEvidence`). Builds a NetworkX `DiGraph` (paper → steps → evidence)
5. **Evaluate Figures** — `FigureEvaluator` runs 4 LLM calls per figure: vision description → expected description → comparison → claim assessment
6. **Evaluate Math** — `MathEvaluator` (LangGraph ReAct agent) uses the MCP calculator server to verify equations with SymPy
7. **Score Papers** _(Librarian pass 2)_ — `Librarian` scores each discovered paper for relevancy (0–1) and convergence (−1 to +1, where negative means the paper contradicts the submitted work and positive means it supports/converges). Results are added to the paper graph.
8. **Compile Results** — LLM synthesizes an `OverAllReview`, calculates a 0–1 confidence score

The backend runs the pipeline as a background task. The frontend polls `/api/pipeline/status/:jobId` every 2 seconds and displays step-by-step progress.

### Confidence Score

The final score averages four metrics:

- Math validity fraction (correct / total equations)
- Figure confirmation ratio (confirmations vs contradictions)
- Librarian convergence score (relevancy-weighted average convergence of related papers, mapped from [−1, +1] to [0, 1])
- Evidence coverage (steps with evidence / total steps)

## API Endpoints

### Auth

| Method | Path                 | Description                       |
| ------ | -------------------- | --------------------------------- |
| POST   | `/api/auth/register` | Create account (or convert guest) |
| POST   | `/api/auth/login`    | Log in (email or username)        |
| POST   | `/api/auth/try`      | Create anonymous guest account    |
| POST   | `/api/auth/refresh`  | Rotate refresh token (cookie)     |
| GET    | `/api/auth/me`       | Current user profile              |
| POST   | `/api/auth/logout`   | Clear refresh cookie              |

### Pipeline

| Method | Path                             | Description                                                             |
| ------ | -------------------------------- | ----------------------------------------------------------------------- |
| POST   | `/api/pipeline/validate`         | Submit paper for validation                                             |
| GET    | `/api/pipeline/status/:job_id`   | Poll job progress (step number + name)                                  |
| GET    | `/api/pipeline/results/:job_id`  | Get completed `ValidationResult`                                        |
| GET    | `/api/pipeline/graph/:job_id`    | Get paper graph (NetworkX node-link JSON)                               |
| GET    | `/api/pipeline/analysis/:job_id` | Get graph analysis (contradictions, invalid math, citation stats, etc.) |
| GET    | `/api/pipeline/jobs`             | List all jobs                                                           |

### Documents

| Method         | Path                                     | Description                         |
| -------------- | ---------------------------------------- | ----------------------------------- |
| GET/POST       | `/api/documents`                         | List owned + shared / create        |
| GET/PUT/DELETE | `/api/documents/:id`                     | Read / update / delete              |
| POST           | `/api/documents/:id/share`               | Share with user (upsert permission) |
| DELETE         | `/api/documents/:id/share/:user_id`      | Revoke share                        |
| GET/POST       | `/api/documents/:id/attachments`         | List / upload attachments           |
| DELETE         | `/api/documents/:id/attachments/:att_id` | Delete attachment                   |

### Workspaces

| Method      | Path                            | Description              |
| ----------- | ------------------------------- | ------------------------ |
| GET/POST    | `/api/workspaces`               | List / create            |
| GET/DELETE  | `/api/workspaces/:id`           | Read / delete            |
| GET         | `/api/workspaces/:id/documents` | List workspace documents |
| POST/DELETE | `/api/workspaces/:id/members`   | Add / remove member      |

### Users

| Method | Path                   | Description                        |
| ------ | ---------------------- | ---------------------------------- |
| GET    | `/api/users/search?q=` | Search by email/username (no auth) |

## Tech Stack

| Layer         | Technology                                                                            |
| ------------- | ------------------------------------------------------------------------------------- |
| Orchestration | LangGraph StateGraph                                                                  |
| LLM           | Claude (Anthropic) via LangChain's `ChatAnthropic` + `with_structured_output()`       |
| Tool servers  | MCP (Model Context Protocol) — advisor server (stdio) + calculator server (SSE/stdio) |
| Math solver   | SymPy via MCP calculator server, backed by SQLite formula table                        |
| Related work  | LanceDB (FTS + vector search) primary, Semantic Scholar API fallback                  |
| Vision        | LangChain `HumanMessage` with image content blocks                                    |
| Backend       | FastAPI, SQLModel (SQLite), JWT HS256 auth                                            |
| Storage       | Local filesystem or MinIO (S3-compatible)                                             |
| Frontend      | React 18, TypeScript, MUI v5, Vite                                                    |
| Themes        | 6 MUI themes (3 light: default/professional/minimal, 3 dark: default/nord/dracula)    |
