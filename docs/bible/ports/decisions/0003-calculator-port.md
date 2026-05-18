---
id: ports-0003
title: `Calculator` port for math verification
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

The `MathEvaluator` agent needs to verify equations extracted from papers. The current implementation calls an MCP-server-hosted calculator (SymPy under the hood) through a custom sync wrapper that runs an asyncio loop in a background thread to bridge between LangGraph's sync execution and the MCP SDK's async surface.

This is functional but invasive: the wrapper, the thread, and the MCP-specific behavior live inside the agent's import surface. The agent should not know that math verification is an MCP server. It should know that there is a `Calculator` it can ask.

## Decision

```python
class Calculator(Protocol):
    async def calculate(self, expression: str) -> CalculationResult: ...

    async def verify(self, equation: str, context: str | None = None) -> VerificationResult: ...

    async def list_formulas(self, domain: str | None = None) -> list[FormulaSummary]: ...

    async def describe_formula(self, formula_id: str) -> FormulaDescription: ...
```

The four methods mirror the MCP server's current tool surface. They are framed in core vocabulary (`verify(equation)`), not protocol vocabulary (`call_tool("verify", {...})`).

The implementing adapter handles transport choice (stdio vs HTTP/SSE), connection pooling, and any background-thread bridging needed for sync callers. The port is async; sync use from LangGraph nodes wraps via the existing helper.

## Consequences

**Easy:**
- The agent receives a `Calculator` in its constructor. It does not import `mcp` or `CalculatorClient`.
- Replacing the MCP calculator with a different math-verification backend (a direct SymPy library call, a different service) is an adapter swap.
- Testing the agent uses a fake `Calculator` that returns canned `VerificationResult`s.

**Hard:**
- The four methods are the *current* tool surface; if the MCP server grows new tools, the port grows new methods, or the new tools stay outside the port (and outside the agent's reach via the port). Each method earns its way in.
- The bridge from async port to LangGraph's sync execution lives in the adapter. The orchestrator does not know about it.

**Forecloses:**
- Direct `mcp` imports anywhere in core. Allowed only inside the MCP-calculator adapter.
- "Just call SymPy directly" shortcuts. SymPy use is encapsulated by the calculator server; the port abstraction is preserved.

## Adapters

- **`McpCalculatorClient`** — current. Wraps the MCP SDK, runs an asyncio loop on a daemon thread when called from a sync context, switches between stdio and HTTP/SSE transports based on config.
- **`InMemoryCalculator`** — test fake. Programmed return values keyed by expression.

See [adapters/driven/decisions/0004-mcp-calculator-client.md](../../adapters/driven/decisions/0004-mcp-calculator-client.md).

## Review trigger

- The math-verification needs of the system grow beyond what MCP-tooled SymPy provides (e.g., numeric solvers, dimensional analysis, unit handling). Add port methods; consider replacing the adapter with one that talks to a more capable service.
- The asyncio-bridge complexity becomes a frequent bug source. At that point either standardize on async execution throughout (no more sync-bridging) or simplify the calculator surface to remove the need.
