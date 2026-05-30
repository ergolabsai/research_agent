# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Shared fakes for agent unit tests.

These fakes satisfy the runtime_checkable Protocols in core.ports without
touching any real LLM, MCP server, or vector DB. Tests assert on the prompts
the agents emit and the calls they make through their ports — the seams the
migration just introduced.
"""

from __future__ import annotations

from typing import Any, Sequence, Type, TypeVar

import pandas as pd
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class FakeLLMClient:
    """In-memory LLMClient. Captures every call and replays scripted responses.

    `structured_responses` is a dict keyed by schema class name; tests push
    a list of pre-built BaseModel instances and FakeLLMClient returns them
    in FIFO order.
    """

    def __init__(
        self,
        structured_responses: dict[str, list[BaseModel]] | None = None,
        text_responses: list[str] | None = None,
        vision_responses: list[str] | None = None,
    ):
        self._structured = {k: list(v) for k, v in (structured_responses or {}).items()}
        self._text = list(text_responses or [])
        self._vision = list(vision_responses or [])
        self.structured_calls: list[tuple[Type[BaseModel], str, str | None]] = []
        self.text_calls: list[tuple[str, str | None]] = []
        self.vision_calls: list[tuple[str, str, str]] = []
        self.bind_tools_calls: list[Sequence[Any]] = []

    def get_structured_output(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: str | None = None,
    ) -> T:
        self.structured_calls.append((schema, prompt, system_prompt))
        queue = self._structured.get(schema.__name__, [])
        if not queue:
            raise AssertionError(
                f"FakeLLMClient has no scripted response for {schema.__name__}"
            )
        return queue.pop(0)  # type: ignore[return-value]

    def invoke_text(self, prompt: str, system_prompt: str | None = None) -> str:
        self.text_calls.append((prompt, system_prompt))
        if not self._text:
            raise AssertionError("FakeLLMClient has no scripted text response")
        return self._text.pop(0)

    def invoke_vision(self, prompt: str, media_type: str, image_data: str) -> str:
        self.vision_calls.append((prompt, media_type, image_data))
        if not self._vision:
            raise AssertionError("FakeLLMClient has no scripted vision response")
        return self._vision.pop(0)

    def bind_tools(self, tools: Sequence[Any]):  # noqa: ANN201 — see comment
        # Returns a Mock-ish object that supports `.invoke({...}, ...)` so the
        # MathEvaluator's react-agent construction in __init__ does not fall
        # over. Tests that actually exercise math evaluation patch the agent
        # itself; this is just to keep `create_react_agent` happy at init.
        self.bind_tools_calls.append(tools)

        class _Bound:
            def bind_tools(self, _tools):
                return self

            def invoke(self, *_a, **_k):
                return {"messages": []}

        return _Bound()


class FakePaperIndex:
    """In-memory PaperIndex. Returns whatever DataFrames the test scripts."""

    def __init__(
        self,
        vector_results: list[pd.DataFrame] | None = None,
        fts_results: list[pd.DataFrame] | None = None,
    ):
        self._vector = list(vector_results or [])
        self._fts = list(fts_results or [])
        self.vector_calls: list[tuple[str, int]] = []
        self.fts_calls: list[tuple[str, int]] = []

    def vector_search(self, query: str, limit: int = 10) -> pd.DataFrame:
        self.vector_calls.append((query, limit))
        return self._vector.pop(0) if self._vector else pd.DataFrame()

    def fts_search(self, query: str, limit: int = 10) -> pd.DataFrame:
        self.fts_calls.append((query, limit))
        return self._fts.pop(0) if self._fts else pd.DataFrame()
