# Research Advisor

A multi-agent system that validates scientific research papers. Paste in a paper, and six specialized AI agents analyze its logical structure, verify math, check citations against Semantic Scholar, evaluate figures, and produce a confidence-scored assessment.

## Architecture

```
Frontend (React + MUI)          Backend (FastAPI)              Pipeline (6 Agents)
========================        =====================          ====================
ValidatePage                    POST /api/pipeline/validate    1. Paper Reader
  - paste paper text     --->   GET  /api/pipeline/status/:id  2. Evidence Finder
  - live progress bar    <---   GET  /api/pipeline/results/:id 3. Figure Evaluator
  - step-by-step results                                       4. Math Evaluator
                                                               5. Citation Checker
DashboardPage                   /api/documents/*               6. Results Compiler
EditorPage                      /api/workspaces/*
Login / Register                /api/auth/*
```

**Data stores:**
- **SQLite** (via SQLModel) -- users, documents, workspaces
- **MongoDB** -- papers, validation results, formula definitions

## Project Structure

```
.
├── advisor_pipeline/           # The 6-agent validation pipeline
│   ├── agents/                 # One module per agent
│   │   ├── base_agent.py       # Abstract base (Instructor + LangChain)
│   │   ├── paper_reader_agent.py
│   │   ├── evidence_finder_agent.py
│   │   ├── figure_evaluator_agent.py   # Claude vision API
│   │   ├── math_evaluator_agent.py     # MCP calculator integration
│   │   ├── citation_checker_agent.py   # Semantic Scholar API
│   │   └── results_compiler_agent.py
│   ├── calculator_server/      # MCP server for symbolic math (SymPy)
│   │   ├── server.py           # HTTP/SSE transport
│   │   ├── server_stdio.py     # Stdio transport
│   │   └── tools/              # Solver, formulas, repository
│   ├── config/settings.py      # Unified settings (shared with backend)
│   ├── models/schemas.py       # Pydantic models for pipeline data
│   ├── database.py             # MongoDB interface
│   └── pipeline.py             # Orchestrator (runs all 6 steps)
│
├── backend/                    # FastAPI application
│   └── app/
│       ├── main.py             # App entry point, CORS, routers
│       ├── models.py           # SQLModel schemas (User, Document, Workspace)
│       ├── security.py         # JWT auth, bcrypt, session management
│       ├── routes/
│       │   ├── auth.py         # Register, login, guest mode, refresh
│       │   ├── documents.py    # CRUD + sharing
│       │   ├── workspaces.py   # CRUD + members
│       │   ├── users.py        # Search
│       │   └── pipeline.py     # Submit validation, poll status, get results
│       └── services/
│           └── pipeline_service.py  # Async job runner with progress tracking
│
├── frontend/                   # React + TypeScript
│   └── src/
│       ├── api/client.ts       # Axios client (auth, documents, pipeline APIs)
│       ├── pages/
│       │   ├── ValidatePage.tsx # Paper validation UI
│       │   ├── DashboardPage.tsx
│       │   ├── EditorPage.tsx
│       │   ├── LandingPage.tsx
│       │   ├── LoginPage.tsx
│       │   └── RegisterPage.tsx
│       ├── components/         # Sidebar, DocumentItem, WorkspaceItem, etc.
│       ├── context/AuthContext.tsx
│       ├── theme/              # Light/dark themes (default, nord, dracula)
│       └── types/index.ts      # TypeScript interfaces
│
├── pyproject.toml              # Python dependencies
├── .env.example                # Environment variable template
└── .gitignore
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB running locally (default: `localhost:27017`)
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
# Change SECRET_KEY to something random
```

### 2. Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# or: pip install -e ".[dev]" for pytest + ruff
```

### 3. Frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Start MongoDB

skip this step if you already have mongo working on your computer

```bash
# To check if you have MongoDB
mongosh

# If using Homebrew:
brew services start mongodb-community

# Or with Docker:
docker run -d -p 27017:27017 mongo
```

### 5. Run

Open three terminals:

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3 (optional): MCP Calculator Server
cd advisor_pipeline/calculator_server
python server.py
```

The frontend runs at `http://localhost:5173` and proxies API calls to the backend.

## How Validation Works

When you submit a paper through the Validate page or API:

1. **Paper Reader** -- Breaks the paper into discrete logical steps with dependencies
2. **Evidence Finder** -- Searches the text for figures, equations, and citations supporting each step
3. **Figure Evaluator** -- If figure files are provided, uses Claude's vision API to check whether figures actually support claimed findings. Falls back to text-only analysis otherwise.
4. **Math Evaluator** -- Identifies formulas, extracts values, and verifies calculations using a SymPy-based MCP solver
5. **Citation Checker** -- Looks up citations via the Semantic Scholar API to check accessibility and whether they support the attributed claims
6. **Results Compiler** -- Synthesizes everything into a final assessment with a 0-1 confidence score

The backend runs this as a background job. The frontend polls for progress and displays results step-by-step.

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Log in |
| POST | `/api/auth/try` | Guest mode |
| POST | `/api/auth/refresh` | Refresh token |
| GET | `/api/auth/me` | Current user |
| POST | `/api/auth/logout` | Log out |

### Pipeline
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/pipeline/validate` | Submit paper for validation |
| GET | `/api/pipeline/status/:job_id` | Poll job progress |
| GET | `/api/pipeline/results/:job_id` | Get completed results |
| GET | `/api/pipeline/history/:paper_id` | All validations for a paper |
| GET | `/api/pipeline/jobs` | List all jobs |

### Documents & Workspaces
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/documents` | List / create documents |
| GET/PUT/DELETE | `/api/documents/:id` | Read / update / delete |
| POST/DELETE | `/api/documents/:id/share` | Share / unshare |
| GET/POST | `/api/workspaces` | List / create workspaces |
| GET/DELETE | `/api/workspaces/:id` | Read / delete |
| POST/DELETE | `/api/workspaces/:id/members` | Add / remove members |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Claude (Anthropic) via Instructor + LangChain |
| Backend | FastAPI, SQLModel, JWT auth |
| Pipeline DB | MongoDB + PyMongo |
| Math solver | SymPy via MCP server |
| Citations | Semantic Scholar API |
| Vision | Anthropic vision API |
| Frontend | React 18, TypeScript, Material-UI, Vite |
| Themes | Light/dark with 6 palettes |
