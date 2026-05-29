# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""McpCalculatorClient — adapter satisfying `core.ports.calculator.Calculator`.

The existing `CalculatorClient` in `advisor_pipeline/mcp_client.py` already
exposes the sync `call_tool` + context-manager surface the port requires,
so this module simply re-exports it under the adapter name. The
asyncio-loop-in-daemon-thread bridge stays put for now; Step 5 moves the
implementation here.
"""

from advisor_pipeline.mcp_client import CalculatorClient as McpCalculatorClient

__all__ = ["McpCalculatorClient"]
