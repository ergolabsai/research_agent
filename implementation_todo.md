# Step 3 (revised): Orchestrator + agents → `core/services/` with injected ports

Companion to [docs/architecture/MIGRATION.md](docs/architecture/MIGRATION.md). Check items off as they land. Each step ends with `make dev` working.

## Prep A — Relocate cross-boundary modules that core will need

*Why: After the orchestrator moves to `core/`, anything it imports must already live in `core/` or be reachable through a port. Prompts and settings are the two non-port imports that would otherwise become boundary violations the moment the orchestrator moves.*

- [x] Move prompt constants (`CONTEXT_MAKER`, `LOGIC_MAPPER`, `EVIDENCE_FINDER`, `RESULTS_COMPILER`, `SYSTEM_PROMPT`) out of `advisor_pipeline/mcp_servers/advisor_server/prompts.py` into `core/services/prompts.py` (or co-locate per-service). The MCP server keeps re-exporting them so the stdio server still works. *Why: orchestrator.py:22-28 imports prompts from `advisor_pipeline.*`; once orchestrator lives in core, that becomes a `core → advisor_pipeline` violation.*
- [x] Create `composition/settings.py` and re-export the existing `Settings` instance. Update `backend/app/security.py:10` and `backend/app/storage.py:5` to import from there. Leave a thin re-export in `advisor_pipeline/config/settings.py` for now so nothing breaks mid-migration. *Why: the final step deletes `advisor_pipeline/`; without redirecting these imports first, the delete strands the backend.*
- [x] Smoke checkpoint: `make dev` still starts; both prompt imports and settings imports resolve.

## Prep B — Define the three new ports (no behavior change)

*Why: today the orchestrator and all three agents reach for module-level globals (`get_llm()`, `_db_connection`, `CalculatorClient()`). Ports make those dependencies explicit and substitutable.*

- [x] Define `core/ports/llm_client.py` — Protocol with `get_structured_output(schema, prompt, system_prompt=None)`, `invoke_text(prompt)`, `invoke_vision(prompt, media_type, image_data)`, and `bind_tools(tools)` (returns a tool-bound LLM for LangGraph's `create_react_agent`). *Why: MathEvaluator (math_evaluator.py:33) needs a tool-bound model for ReAct; exposing `bind_tools` on the port keeps the contract intact without a `raw_llm()` escape hatch that will erode the boundary.*
- [x] Define `core/ports/calculator.py` — Protocol with **synchronous** context-manager semantics (`__enter__`/`__exit__`) plus the `tools` surface the math evaluator actually uses. *Why: orchestrator.py:212 currently uses `with CalculatorClient() as client:` (sync). The asyncio-loop-in-daemon-thread bridge stays inside the adapter; the port stays sync to match current usage.*
- [x] Define `core/ports/paper_index.py` — Protocol with `vector_search(query, k)` and `fts_search(query, k)` returning the existing result shape used by librarian.py:37. *Why: today the Librarian imports `fts_search` / `vector_search` directly from `utils/lancedb_search.py`, which holds module-level `_db_connection` / `_table` globals.*

## Prep C — Build thin adapter shims (still wrap existing globals)

*Why: one-commit refactor that costs nothing — adapters satisfy the new ports by delegating to current free functions. Any regression is structurally impossible because no consumer has switched yet.*

- [x] `adapters/driven/llm/anthropic.py` — `ChatLLMClient` class whose methods delegate to existing `advisor_pipeline.llm` free functions. Name it `ChatLLMClient` (not `AnthropicLLMClient`) so the OpenRouter branch in `_build_llm` doesn't force a rename later. *Why: `_build_llm` already conditionally wires Anthropic or OpenRouter; the adapter covers both.*
- [x] `adapters/driven/mcp/calculator_client.py` — move `CalculatorClient` here unchanged. Threading bridge stays put.
- [x] `adapters/driven/paper_index/lancedb.py` — `LanceDBPaperIndex` class delegating to existing `vector_search` / `fts_search`. Module-level `_db_connection` lives on for now.
- [x] Smoke checkpoint: wire all three adapters into `composition/container.py` as singletons (don't inject anywhere yet). Confirm `make dev` still starts. *Why: proves the new ports + adapters import cleanly before any consumer changes.*

## Step 1 — Migrate agents (one at a time)

*Why: smaller diffs than moving and injecting in one commit. File relocation is a mechanical follow-up once injection is proven.*

- [ ] `FigureEvaluator` → constructor takes `LLMClient`. Replace `invoke_text(...)`, `invoke_vision(...)`, `get_structured_output(...)` with `self._llm.*` calls. **Do not move the file yet.**
- [ ] `Librarian` → constructor takes `LLMClient` and `PaperIndex`. Drop the `lancedb_search` import.
- [ ] `MathEvaluator` → constructor takes `LLMClient` and `Calculator`. Replace `get_llm().bind_tools(...)` with `self._llm.bind_tools(...)`.
- [ ] Add one fixture-driven test per agent using a mock `LLMClient` (and `PaperIndex` / `Calculator` where applicable). *Why: the whole point of DI is testability — without one test exercising the seam, the next refactor will quietly re-couple. Lock in current behavior with a fixture before any file moves.*
- [ ] Smoke checkpoint: instantiate agents in `composition/container.py` via the new constructors; existing orchestrator still works (it imports agents lazily inside node functions, so a constructor mismatch surfaces immediately).

## Step 2 — Migrate the orchestrator

*Why: today's orchestrator re-imports agents inside each node function and instantiates them per-run (orchestrator.py:177, 202, 229, 255). Centralizing in `__init__` removes hidden coupling and lets the use case build the orchestrator once.*

- [ ] Turn `AdvisorOrchestrator` into a class with `__init__(llm, calculator, paper_index, on_step_complete=None)`. Node functions become methods. Agents are constructed once in `__init__` (`self._figure_eval`, `self._math_eval`, `self._librarian`).
- [ ] Rewire `_build_graph` and `_build_graph_with_callbacks` (orchestrator.py:593-602) to reference bound methods instead of module-level functions. Update the `NODE_FUNCS` dict accordingly. *Why: easy to miss in the "turn into a class" diff; the callback wrapper currently captures free-function references by name.*
- [ ] Replace direct `invoke_text` / `get_structured_output` calls inside nodes with `self._llm.*` calls.
- [ ] Smoke checkpoint: orchestrator instantiated in container; `LegacyPipelineRunner` updated to use it. End-to-end `/api/pipeline/validate` returns 200 + job_id.

## Step 3 — Move files into `core/`

*Why: the orchestrator can't move to `core/` until everything it imports also lives in core or behind a port. Prep A handled prompts and settings; this is the mechanical relocation.*

- [ ] `advisor_pipeline/orchestrator.py` → `core/services/orchestrator.py`. Update all imports across `composition/`, `backend/app/`, tests.
- [ ] `advisor_pipeline/agents/*.py` → `core/services/`. Drop the `agents/` subdir; "agent" is an implementation detail.
- [ ] `advisor_pipeline/models/paper_graph.py` → `core/domain/graph.py`. Pure NetworkX wrapper, no external deps.
- [ ] Schemas referenced by orchestrator (`PaperStructure`, `Evidence`, `StepEvidence`, `OverAllReview`, etc.) → `core/contracts/validation.py`. Pull over whatever isn't already there. `models/schemas.py` gets emptied.
- [ ] Smoke checkpoint: re-run `/api/pipeline/validate` end-to-end. Same response shape. Confirm import-linter is green for the new contract.

## Step 4 — Replace `LegacyPipelineRunner` and split `pipeline_service.py`

*Why: MIGRATION.md flags more than just the runner — `pipeline_service.py` also owns the `_graphs` in-memory cache and the storage-backed figure hydration. Those need homes before the file can shrink.*

- [ ] `adapters/driven/pipeline_runner/inline.py` — constructor takes the orchestrator. `submit()` schedules the run via **`asyncio.to_thread(orchestrator.run, ...)`** (or a dedicated `ThreadPoolExecutor`). **Do not use `asyncio.create_task`** — `graph.invoke()` (orchestrator.py:692) is synchronous and would block the event loop for the entire pipeline run. *Why: current `pipeline_service` uses a ThreadPool; matching that prevents regression.*
- [ ] Wire `on_step_complete` to a `JobStore`-backed progress callback.
- [ ] Define `core/ports/graph_cache.py` (small `get`/`set`/`evict` Protocol). Adapter: `adapters/driven/graph_cache/memory.py` wrapping an LRU dict. Move the `_graphs: dict[str, nx.DiGraph]` cache from `pipeline_service.py:54-55` into the adapter. *Why: keeping the cache as a module global re-introduces the same singleton problem the rest of step 3 is removing.*
- [ ] Move figure-hydration logic (storage → figure dict) into a `FigureHydrator` adapter under `adapters/driven/object_storage/`, or fold it into the existing storage adapter — whichever keeps the use case's call site cleanest. *Why: hydration touches infrastructure (object storage) and doesn't belong in `core/`.*
- [ ] Swap `composition/container.py` to construct the new runner, graph cache, and hydrator. Delete `LegacyPipelineRunner` and its `_backfill_paper_context` helper.
- [ ] Smoke checkpoint: end-to-end validate still works; per-step progress still appears in `PipelineStepLog`; figures still surface in `GET /api/pipeline/figures/:jobId`.

## Step 5 — Dismantle the singletons

*Why: with every consumer routed through ports, the module-level state has no remaining callers and can be deleted.*

- [ ] Delete `_llm = _build_llm()` and `get_llm()` from `advisor_pipeline/llm.py`. Move `_build_llm` body into `ChatLLMClient.__init__`. Move `@retry`-decorated helpers onto adapter methods (tenacity works on methods fine).
- [ ] Delete `_db_connection` / `_table` globals from `lancedb_search.py`. State moves onto `LanceDBPaperIndex` instance attributes.
- [ ] Delete `CalculatorClient` module-level state. Threading bridge moves onto the adapter instance.
- [ ] Delete `advisor_pipeline/agents/`, `advisor_pipeline/orchestrator.py`, `advisor_pipeline/models/`, and `advisor_pipeline/utils/lancedb_search.py` once nothing imports them. Also remove the `advisor_pipeline/config/settings.py` re-export shim added in Prep A.
- [ ] `advisor_pipeline/` shrinks to MCP servers only.

## Finalize

- [ ] Tighten import-linter contracts: forbid `core → adapters` and `core → advisor_pipeline`. Per process/0001.
- [ ] Run the agent-level fixture tests from Step 1 plus an end-to-end smoke against the real pipeline; compare confidence score + step counts against a pre-migration baseline. *Why: MIGRATION.md's done-criterion explicitly calls for "no regression in the figure / math / librarian step outputs."*
- [ ] Update `docs/architecture/MIGRATION.md` to mark step 3 done.
- [ ] Strike completed lines from `todo.txt`.
