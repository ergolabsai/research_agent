# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Transitional port for kicking off the validation pipeline.

The orchestrator is core territory (see capabilities/validation/0002), but during
MIGRATION step 2 the legacy `advisor_pipeline.orchestrator` and its singleton
dependencies (LLM, calculator, paper index) are not yet movable. A driven adapter
implementing this port wraps the legacy `pipeline_service.run_validation_job` so
`ValidatePaper` can fire it without importing from `advisor_pipeline` directly.

This port disappears in MIGRATION step 3 when the orchestrator moves to
`core/services/`; the use case then calls the orchestrator directly.
"""

from typing import Protocol, runtime_checkable

from core.contracts.auth import Principal
from core.contracts.jobs import Job
from core.contracts.paper import Paper


@runtime_checkable
class PipelineRunner(Protocol):
    async def submit(self, job: Job, paper: Paper, principal: Principal) -> None:
        """Start the validation pipeline for a job. Returns immediately (fire-and-forget).

        Progress and final results are written through `JobStore` by the runner.
        The full `Job` is passed (not just the id) so the runner has paper_id, title,
        and timestamps without an extra fetch.
        """
        ...
