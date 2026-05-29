# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Calculator port.

Minimal sync surface the MathEvaluator actually consumes from the MCP
calculator client. The asyncio-loop-in-daemon-thread bridge that the real
adapter uses stays hidden behind this Protocol — the math evaluator only
sees `call_tool` and the sync context-manager lifecycle.

The port is synchronous because the MathEvaluator runs inside LangGraph's
sync `create_react_agent` execution and uses `with CalculatorClient() as
client:` today (orchestrator.py).
"""

from types import TracebackType
from typing import Protocol, runtime_checkable


@runtime_checkable
class Calculator(Protocol):
    def call_tool(self, name: str, **kwargs: object) -> dict:
        """Invoke an MCP tool by name. Returns the parsed JSON result."""
        ...

    def __enter__(self) -> "Calculator": ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
