# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Re-export of prompt templates for the Advisor MCP server.

The canonical definitions live in `core.services.prompts`. This module keeps
the historical import path stable for the stdio MCP server.
"""

from core.services.prompts import (  # noqa: F401
    CLAIM_ASSESSOR,
    CONTEXT_MAKER,
    EVIDENCE_FINDER,
    FIGURE_COMPARATOR,
    FIGURE_DESCRIBER,
    FIGURE_EXPECTED,
    LIBRARIAN_CONTEXT,
    LIBRARIAN_QUERY_CRAFTER,
    LIBRARIAN_SCORER,
    LOGIC_MAPPER,
    MATH_REPORTER,
    MATH_VERIFIER,
    PROMPT_REGISTRY,
    RESULTS_COMPILER,
    SYSTEM_PROMPT,
)
