# The Advisor — Architecture Refactor Spec

## Goal

Refactor The Advisor from a rigid linear pipeline into a flexible agent system where:
- **LangGraph** orchestrates the workflow with conditional routing (not just linear edges)
- **MCP servers** expose all tools AND prompt templates, so the orchestrator can dynamically choose what to invoke
- **Existing schemas, agents, and logic are preserved** — this is a restructuring, not a rewrite from scratch

## Current Architecture (what exists)

```
advisor_pipeline/
├── pipeline.py              # LangGraph StateGraph — strictly linear: load→map_logic→find_evidence→evaluate_figures→compile
├── agents/
│   ├── base_agent.py        # BaseAgent ABC with instructor client, LangChain LLM, vision, structured output
│   ├── logic_mapping_agent.py    # Extracts PaperStructure from paper text (no tools)
│   ├── evidence_finder_agent.py  # Finds evidence per logical step (no tools)
│   ├── figure_evaluator_agent.py # Vision-based figure evaluation (no tools, uses direct Anthropic API for images)
│   ├── math_evaluator_agent.py   # MCP calculator integration (has LangChain tools)
│   ├── citation_checker_agent.py # Semantic Scholar API (has LangChain tools)
│   └── results_compiler_agent.py # Synthesizes everything into ValidationResult (no tools)
├── models/
│   └── schemas.py           # All Pydantic schemas (PaperStructure, Evidence, FigureEvaluation, etc.)
├── calculator_server/       # Existing MCP server for math/physics formulas (HTTP/SSE transport)
│   ├── server.py
│   └── tools/               # Formula DB, solver, etc.
├── config/
│   └── settings.py          # Pydantic settings from .env
└── database.py              # MongoDB interface (papers + validations collections) [NOTE: never implemented; replaced by SQLite]
```

### Key characteristics of current code:
1. **Pipeline is strictly linear** — `START → load_paper → map_logic → find_evidence → evaluate_figures → compile_results → END`. No conditional edges, no loops, no backtracking.
2. **BaseAgent has two LLM clients** — `instructor` (for structured output) and `ChatAnthropic` (for LangChain agent loops). This is redundant and should be consolidated to just `ChatAnthropic`.
3. **Most agents don't use tools** — only MathEvaluator and CitationChecker have LangChain tools. The others just call `get_structured_output()` or `invoke_llm()`.
4. **Evidence finder has a hardcoded `break` at step 2** — `if step.step_number > 2: break` (line in evidence_finder_agent.py). This was for testing and should be removed.
5. **Math and citation steps are disabled** in the pipeline (commented out in PipelineState and not wired in the graph).
6. **Figure evaluator uses raw Anthropic API** for vision (not through LangChain), then structures output via instructor.

### Critical refactor: Drop `instructor`, use `ChatAnthropic.with_structured_output()`
The current codebase uses **two separate LLM clients**: an `instructor`-wrapped Anthropic client for structured Pydantic output, and a `ChatAnthropic` instance for LangChain agent loops. This is redundant.

**Replace all `instructor` usage with LangChain's `with_structured_output()`:**

```python
# OLD (instructor) — REMOVE THIS PATTERN
from instructor import from_anthropic
client = from_anthropic(Anthropic(api_key=...))
result = client.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": prompt}],
    response_model=PaperStructure
)

# NEW (LangChain) — USE THIS PATTERN
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model_name="claude-sonnet-4-20250514")
structured_llm = llm.with_structured_output(PaperStructure)
result = structured_llm.invoke(prompt)  # returns validated PaperStructure
```

This works because `with_structured_output()` uses the same tool-calling trick as instructor (converts the Pydantic model to a tool schema, forces the LLM to call it, parses the result back).

**For vision + structured output** (figure evaluator), LangChain handles this natively:

```python
from langchain_core.messages import HumanMessage

structured_llm = llm.with_structured_output(FigureDescription)
result = structured_llm.invoke([
    HumanMessage(content=[
        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
        {"type": "text", "text": "Describe this scientific figure in detail..."}
    ])
])
```

**Validation retry handling:** Unlike instructor, `with_structured_output()` does not auto-retry on Pydantic validation failures. In practice Claude almost never violates well-defined Pydantic constraints, but add a simple retry wrapper for safety:

```python
from tenacity import retry, stop_after_attempt, retry_if_exception_type
from pydantic import ValidationError

@retry(stop=stop_after_attempt(3), retry=retry_if_exception_type(ValidationError))
def get_structured_output(llm, schema, prompt):
    structured_llm = llm.with_structured_output(schema)
    return structured_llm.invoke(prompt)
```

**Remove from `pyproject.toml`:** `instructor>=1.0.0`
**Add to `pyproject.toml`:** `tenacity>=8.0.0`

## Target Architecture

```
advisor_pipeline/
├── orchestrator.py          # LangGraph StateGraph with conditional edges
├── mcp_servers/
│   ├── advisor_server/      # NEW: MCP server exposing advisor prompts + paper/evidence DB tools
│   │   ├── server.py
│   │   ├── prompts.py       # Prompt templates as MCP prompts
│   │   └── tools.py         # Paper DB queries, evidence DB queries
│   └── calculator_server/   # EXISTING: Math/physics calculator (move from current location)
│       ├── server.py
│       └── tools/
├── agents/                  # Simplified — agents become thin wrappers or are absorbed into orchestrator
│   └── ...
├── models/
│   └── schemas.py           # KEEP AS-IS (with minor additions)
├── config/
│   └── settings.py          # KEEP AS-IS
└── (database.py removed — persistence is handled by SQLite via SQLModel)
```

### Core Idea

The four conceptual nodes from the diagram map to this flow:

```
┌─────────────┐    ┌────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│ Make Context │───▶│ Map Logic  │───▶│ Evidence Evaluator  │───▶│ Compile Evidence │
│             │    │            │    │ (loop over steps)    │    │                  │
│ Prompt:     │    │ Prompt:    │    │ Prompt: Check        │    │ Prompt: Compile  │
│  Librarian  │    │  Logic     │    │  evidence            │    │  evidence        │
│ Schema:     │    │  mapper    │    │ Schema:              │    │ Schema:          │
│  Relevant   │    │ Schema:    │    │  LogicEvaluation()   │    │  String()        │
│  Papers()   │    │  LogicMap( │    │  EvidenceEvaluation()│    │  CompiledEvid()  │
│  Contrad.   │    │  Evidence  │    │ Tools:               │    │ Tools: None      │
│  Papers()   │    │  ())       │    │  Evidence DB         │    │                  │
│  String()   │    │ Tools:     │    │  Evidence prompt type│    │                  │
│ Tools:      │    │  None      │    │                      │    │                  │
│  Paper DB   │    │            │    │                      │    │                  │
└─────────────┘    └────────────┘    └─────────────────────┘    └──────────────────┘
```

**But** — unlike the current linear pipeline, the orchestrator should support:
- **Evidence Evaluator looping back to Make Context** if it realizes it needs more papers or context
- **Map Logic requesting additional context** if the paper's argument structure is unclear
- **Parallel evaluation** of figures, math, and citations within the Evidence Evaluator step
- **The orchestrator deciding** which evaluation types to run based on what evidence was found (e.g., skip math eval if no math evidence)

## Detailed Design

### 1. MCP Advisor Server (`mcp_servers/advisor_server/`)

This is the new centerpiece. It exposes:

#### Prompts (as MCP prompt templates)
Each current agent's prompt becomes an MCP prompt that the orchestrator can request:

| MCP Prompt Name | Current Source | Input Args | Description |
|----------------|---------------|------------|-------------|
| `librarian` | (new) | `paper_text`, `query` | Finds relevant context, papers, contradictory evidence |
| `logic_mapper` | `logic_mapping_agent.py` prompt | `paper_text` | Extracts logical argument structure |
| `evidence_finder` | `evidence_finder_agent.py` prompt | `paper_structure`, `paper_text`, `step`, `figure_names` | Finds evidence for a single logical step |
| `figure_describer` | `figure_evaluator_agent._describe_figure()` | `figure_image` (base64) | Vision: describe what figure actually shows |
| `figure_expected` | `figure_evaluator_agent._describe_expected()` | `figure_name`, `paper_text` | Text-only: what figure should show |
| `figure_comparator` | `figure_evaluator_agent._compare_descriptions()` | `actual_desc`, `expected_desc` | Compare actual vs expected |
| `claim_assessor` | `figure_evaluator_agent._assess_claim()` | `figure_name`, `actual`, `expected`, `comparison`, `claim`, `paper_text` | Assess claim validity |
| `math_verifier` | `math_evaluator_agent.py` prompt | `equation_ref`, `context`, `claim` | Verify math with calculator |
| `citation_verifier` | `citation_checker_agent.py` prompt | `citation`, `claim`, `context` | Verify citation supports claim |
| `results_compiler` | `results_compiler_agent.py` prompt | `paper_structure`, `step_evidence`, `figure_evals`, `math_evals`, `citation_checks` | Synthesize final assessment |

#### Tools (as MCP tools)

| MCP Tool Name | Current Source | Description |
|--------------|---------------|-------------|
| `load_paper` | `pipeline._node_load_paper()` | Load paper text + figures from disk |
| `search_semantic_scholar` | `citation_checker_agent.search_paper_database()` | Search for papers |
| `get_paper_abstract` | `citation_checker_agent.get_paper_abstract()` | Get abstract via DOI/ID |
| `check_paper_accessibility` | `citation_checker_agent.check_accessibility()` | Check if paper is open access |
| `extract_doi` | `citation_checker_agent.extract_doi()` | Extract DOI from citation text |

> **Note (post-refactor):** The originally planned `query_paper_db`, `save_paper`, `query_evidence_db`, and `save_validation` tools (backed by MongoDB `database.py`) were never implemented. Pipeline jobs and step logs are persisted via SQLite/SQLModel in the backend instead.

The **calculator MCP server** remains separate (it already works) and continues to provide `calculate`, `verify`, `list_formulas`, `describe_formula`.

### 2. LangGraph Orchestrator (`orchestrator.py`)

Replace the current linear `AdvisorPipeline` with a `StateGraph` that has conditional edges.

#### State Definition

```python
class AdvisorState(TypedDict, total=False):
    # Inputs
    paper_id: str
    paper_folder: Path
    save_to_db: bool
    bibliography: dict[str, str]
    
    # Paper content (populated by make_context)
    paper_text: str
    figures: dict[str, dict[str, str]]  # name -> {data, media_type}
    
    # Logic mapping output
    paper_structure: PaperStructure
    
    # Evidence (populated by evidence evaluator, may grow if context loops back)
    step_evidence: list[StepEvidence]
    
    # Evaluation results (populated in parallel by sub-evaluators)
    figure_evaluations: list[FigureEvaluation]
    math_evaluations: list[MathEvaluation]
    citation_checks: list[CitationCheck]
    
    # Control flow
    needs_more_context: bool          # Set by evidence evaluator to loop back
    context_requests: list[str]       # What additional context is needed
    evaluation_types_needed: list[str] # ["figure", "math", "citation"] — determined by evidence found
    
    # Final output
    validation_result: ValidationResult
```

#### Graph Structure

```python
workflow = StateGraph(AdvisorState)

# Nodes
workflow.add_node("make_context", make_context_node)
workflow.add_node("map_logic", map_logic_node)
workflow.add_node("find_evidence", find_evidence_node)
workflow.add_node("route_evaluations", route_evaluations_node)
workflow.add_node("evaluate_figures", evaluate_figures_node)
workflow.add_node("evaluate_math", evaluate_math_node)
workflow.add_node("check_citations", check_citations_node)
workflow.add_node("compile_results", compile_results_node)

# Edges
workflow.add_edge(START, "make_context")
workflow.add_edge("make_context", "map_logic")
workflow.add_edge("map_logic", "find_evidence")

# Conditional: evidence evaluator can loop back or proceed
workflow.add_conditional_edges(
    "find_evidence",
    should_loop_back,  # returns "make_context" or "route_evaluations"
    {"make_context": "make_context", "route_evaluations": "route_evaluations"}
)

# Route to appropriate evaluators based on evidence types found
workflow.add_conditional_edges(
    "route_evaluations",
    get_evaluation_branches,  # returns list of next nodes
    {"evaluate_figures": "evaluate_figures", "evaluate_math": "evaluate_math", 
     "check_citations": "check_citations", "compile_results": "compile_results"}
)

# All evaluators lead to compile
workflow.add_edge("evaluate_figures", "compile_results")
workflow.add_edge("evaluate_math", "compile_results")
workflow.add_edge("check_citations", "compile_results")
workflow.add_edge("compile_results", END)
```

#### Node Implementation Pattern

Each node should:
1. Connect to the appropriate MCP server(s)
2. Use the MCP prompt template to construct the LLM call
3. Use the MCP tools if needed
4. Return structured output using `ChatAnthropic.with_structured_output()` and existing Pydantic schemas
5. Update state

```python
from langchain_anthropic import ChatAnthropic
from tenacity import retry, stop_after_attempt, retry_if_exception_type
from pydantic import ValidationError

llm = ChatAnthropic(model_name=settings.model_name, temperature=settings.temperature)

@retry(stop=stop_after_attempt(3), retry=retry_if_exception_type(ValidationError))
def get_structured(schema, prompt):
    """Call LLM with structured output, with retry on validation failure."""
    return llm.with_structured_output(schema).invoke(prompt)

async def map_logic_node(state: AdvisorState) -> dict:
    """Use the logic_mapper MCP prompt to extract paper structure."""
    # Get prompt template from MCP advisor server
    prompt = await mcp_client.get_prompt("logic_mapper", {
        "paper_text": state["paper_text"]
    })
    
    # Call LLM with structured output via LangChain
    paper_structure = get_structured(PaperStructure, prompt)
    
    return {"paper_structure": paper_structure}
```

For **vision calls** (figure evaluator), use LangChain's native multimodal message support:

```python
from langchain_core.messages import HumanMessage

async def describe_figure(figure_data: dict) -> str:
    """Use vision to describe what a figure actually shows."""
    response = llm.invoke([
        HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": f"data:{figure_data['media_type']};base64,{figure_data['data']}"}},
            {"type": "text", "text": "Describe this scientific figure in detail..."}
        ])
    ])
    return response.content
```

### 3. Agent Simplification

With prompts and tools moved to MCP servers and `instructor` replaced by `ChatAnthropic.with_structured_output()`, the agents become much thinner. There are two paths:

**Option A: Absorb agents into orchestrator nodes.** The node functions directly call MCP prompts, use `llm.with_structured_output(Schema)` for structured responses, and call MCP tools. No separate agent classes needed. This is simpler but less modular.

**Option B: Keep thin agent wrappers.** Each agent class holds its MCP client reference, schema type, and a single `ChatAnthropic` instance, with a simple `run()` method that fetches the prompt from MCP, calls `with_structured_output()`, and returns the Pydantic model. No more dual-client pattern.

**Recommendation: Option A for toolless agents, Option B for agents with tools (math, citations).** The figure evaluator is a special case — it needs vision API access via LangChain's multimodal messages, so it should remain a thin wrapper that handles the multi-step figure evaluation flow (describe → expect → compare → assess), using `HumanMessage` with image content for the vision step and `with_structured_output()` for the structured comparison/assessment steps.

### 4. Schema Changes

Keep all existing schemas in `models/schemas.py`. Add:

```python
class ContextRequest(BaseModel):
    """Request for additional context from the evidence evaluator."""
    reason: str = Field(description="Why more context is needed")
    query: str = Field(description="What to search for")
    related_step: int = Field(description="Which logical step needs more context")

class EvaluationRouting(BaseModel):
    """Determines which evaluation types to run."""
    has_figure_evidence: bool
    has_math_evidence: bool  
    has_citation_evidence: bool
    figure_count: int
    math_count: int
    citation_count: int
```

### 5. MCP Server Implementation Notes

Use the **stdio transport** for the advisor MCP server (matching how Claude Code typically connects to MCP servers). The calculator server can stay on HTTP/SSE since it already works.

The advisor MCP server should use `mcp` library's prompt and tool decorators:

```python
from mcp.server import Server
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent

server = Server("advisor-server")

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="logic_mapper",
            description="Extract logical argument structure from a paper",
            arguments=[
                PromptArgument(name="paper_text", description="Full paper text", required=True)
            ]
        ),
        # ... other prompts
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict) -> list[PromptMessage]:
    if name == "logic_mapper":
        return [PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"""Analyze the following research paper. Identify:
1. The paper's title
2. The paper's primary claim or thesis
3. The ordered logical steps of the argument...

Paper text:
{arguments['paper_text']}"""
            )
        )]
```

### 6. Configuration Updates

Add to `.env` / `settings.py`:

```python
# MCP Servers
advisor_mcp_command: str = "python -m advisor_pipeline.mcp_servers.advisor_server.server"
calculator_mcp_command: str = "python -m advisor_pipeline.calculator_server.server_stdio"
```

## Migration Steps (for Claude Code)

Execute these in order:

### Phase 1: Create MCP Advisor Server
1. Create `advisor_pipeline/mcp_servers/` directory structure
2. Move calculator_server under `mcp_servers/`
3. Create `advisor_server/prompts.py` — extract all prompt strings from current agents into MCP prompt templates
4. Create `advisor_server/tools.py` — wrap database operations and citation tools as MCP tools
5. Create `advisor_server/server.py` — stdio transport, registers prompts and tools
6. Test: verify the MCP server starts and lists all prompts/tools

### Phase 2: Refactor Orchestrator
1. Create `orchestrator.py` with the new `AdvisorState` and conditional graph
2. Implement each node function, using MCP clients to get prompts and call tools
3. Implement routing logic (`should_loop_back`, `get_evaluation_branches`)
4. Wire up structured output using `ChatAnthropic.with_structured_output()` with Pydantic schemas
5. Test: run the new orchestrator on a paper and compare output to the old pipeline

### Phase 3: Simplify Agents & Drop Instructor
1. Remove `instructor` dependency from `pyproject.toml`, add `tenacity>=8.0.0`
2. Remove `base_agent.py` entirely — the dual-client pattern and ABC are no longer needed
3. Create a shared utility module (`advisor_pipeline/llm.py`) with:
   - A single `ChatAnthropic` instance configured from settings
   - A `get_structured_output(schema, prompt)` helper using `with_structured_output()` + tenacity retry
   - A `invoke_vision(prompt, media_type, image_data)` helper using LangChain's multimodal `HumanMessage`
4. For toolless agents (logic_mapper, evidence_finder, results_compiler): absorb into orchestrator nodes using the shared LLM utilities
5. For figure_evaluator: refactor to use `llm.invoke()` with `HumanMessage` image content for vision, and `llm.with_structured_output()` for Comparison/FigureClaimAssessment
6. For math_evaluator and citation_checker: keep as thin wrappers that use MCP tools + `with_structured_output()`
7. Remove all `import instructor` and `from anthropic import Anthropic` (direct client) references
8. Remove unused code

### Phase 4: Enable Disabled Steps
1. Re-enable math evaluation in the pipeline
2. Re-enable citation checking in the pipeline  
3. Remove the `if step.step_number > 2: break` hack in evidence_finder
4. Test full pipeline with all evaluation types

### Phase 5: Clean Up
1. Update `pyproject.toml` with any new dependencies
2. Update imports throughout
3. Run linting
4. Update `README.md`

## Files to Preserve (do not rewrite)
- `models/schemas.py` — only add new schemas, don't modify existing ones
- `calculator_server/tools/` — keep all calculator tool implementations (now backed by SQLite instead of MongoDB)
- `config/settings.py` — only add new settings
- `backend/` — don't touch the web backend
- `frontend/` — don't touch the frontend

## Files to Significantly Refactor
- `pipeline.py` → `orchestrator.py` (new graph structure)
- `agents/base_agent.py` (simplify or remove)
- `agents/logic_mapping_agent.py` (absorb into orchestrator)
- `agents/evidence_finder_agent.py` (absorb into orchestrator)
- `agents/results_compiler_agent.py` (absorb into orchestrator)

## Files to Lightly Refactor
- `agents/figure_evaluator_agent.py` (thin wrapper, remove BaseAgent inheritance)
- `agents/math_evaluator_agent.py` (thin wrapper using MCP calculator)
- `agents/citation_checker_agent.py` (thin wrapper using MCP advisor tools)

## Key Constraints
- **Python 3.11+** (already required)
- **Anthropic Claude** as the LLM (keep using `claude-sonnet-4-20250514` default)
- **LangChain `ChatAnthropic` as the sole LLM client** — use `with_structured_output()` for all Pydantic schema enforcement. Do NOT use `instructor` or direct `Anthropic()` client.
- **`tenacity`** for retry logic on structured output validation failures
- **SQLite** for persistence (via SQLModel; MongoDB has been removed)
- **MCP protocol** for server communication
- **Pydantic v2** for all schemas
- Keep the project installable via `pip install -e .`
