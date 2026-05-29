# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""LLMClient port.

Replaces the module-level singleton in `advisor_pipeline/llm.py`. Agents and
the orchestrator depend on this Protocol; a concrete `ChatLLMClient` adapter
(Anthropic or OpenRouter) is injected in `composition/`.
"""

from typing import Any, Protocol, Sequence, Type, TypeVar, runtime_checkable

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    def get_structured_output(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: str | None = None,
    ) -> T: ...

    def invoke_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str: ...

    def invoke_vision(
        self,
        prompt: str,
        media_type: str,
        image_data: str,
    ) -> str: ...

    def bind_tools(self, tools: Sequence[Any]) -> BaseChatModel:
        """Return a tool-bound LangChain chat model.

        Documented infrastructure seam: LangGraph's `create_react_agent`
        consumes a `BaseChatModel`, so the port hands one back rather than
        wrapping every ReAct step. Per ADR capabilities/validation/0002
        ("LangGraph in core"), this is the one place a LangChain type is
        permitted to surface through a core port.
        """
        ...
