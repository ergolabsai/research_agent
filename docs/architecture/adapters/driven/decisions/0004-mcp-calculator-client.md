---
id: adapters-driven-0004
title: MCP calculator client as the `Calculator` adapter
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Math verification needs a backend. SymPy is the obvious library; the question is *how* the agent reaches it. Three structures are possible:

1. **Direct import** — the agent calls SymPy directly.
2. **In-process service** — a thin wrapper around SymPy lives in the same process.
3. **MCP server** — SymPy is wrapped by an MCP server; the agent calls it via the MCP protocol.

The system chose option 3 early in the project as a deliberate bet on MCP as the future of LLM-tool integration. The advisor pipeline benefits because the calculator becomes a tool an LLM agent can use directly (via LangGraph's tool-calling) rather than being one-off Python code.

## Decision

Implement `Calculator` with an `McpCalculatorClient` adapter that talks to the calculator MCP server. The MCP server is a separate process (stdio in dev, HTTP/SSE in production) under `mcp_servers/calculator_server/`.

The adapter:

- Manages the asyncio loop in a background daemon thread so it can serve sync callers (LangGraph nodes run sync).
- Selects transport (stdio vs SSE) from settings.
- Wraps each tool call (`calculate`, `verify`, `list_formulas`, `describe_formula`) as a port method.

Current implementation: `advisor_pipeline/mcp_client.py` (will move to `adapters/driven/mcp/calculator_client.py`).

## Consequences

**Easy:**
- The calculator is available *both* as a port to the agent and as a tool the LLM can call directly via LangGraph's ReAct agent. Same backend; two front doors.
- The MCP server is testable in isolation. The adapter is testable against a fake MCP server.
- Adding new math tools means adding them to the MCP server; the adapter surfaces them via new port methods.

**Hard:**
- The async-in-daemon-thread bridge is a subtle piece of code. It must not leak threads, must shut down cleanly, and must not deadlock under cancellation. Document and unit-test thoroughly.
- MCP is a relatively young protocol. Spec changes may force adapter updates.
- Inter-process communication adds latency compared to a direct SymPy import.

**Forecloses:**
- Direct SymPy imports in core. SymPy is allowed in core ([0003 — Core has no I/O](../../../decisions/0003-core-has-no-io.md)'s allow-list), but the *math verification capability* lives behind the port — domain `core/domain/` code may use SymPy for pure-math value objects (e.g., simplifying a formula), but verification goes through the port.

## Alternatives considered

- **Direct SymPy import in the math evaluator** — viable; simpler. Rejected because it loses the LLM-tool-use benefit (the LLM cannot call SymPy directly without a tool surface), and because the MCP server is already useful in other contexts (an MCP-aware client tool, e.g., Claude Desktop, can use it directly).
- **A bespoke RPC interface (gRPC, FastAPI)** — rejected. MCP is the bet; adding a parallel interface for the same thing is redundant.

## Review trigger

- MCP protocol changes make the adapter brittle.
- The async-bridge complexity becomes a frequent bug source — at that point either standardize on async execution throughout (removing the bridge need) or simplify.
- A direct in-process math library becomes faster, cheaper, and equally LLM-callable. At that point the MCP layer is removable.
