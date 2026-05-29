# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""ChatLLMClient — adapter satisfying `core.ports.llm_client.LLMClient`.

This is a thin shim over the existing free functions in
`advisor_pipeline/llm.py`. The retry decorators and the
`ChatAnthropic`/OpenRouter construction live there for now; Step 5 moves
that body into `__init__` and deletes the free functions.

Named `ChatLLMClient` (not `AnthropicLLMClient`) because `_build_llm` in
`advisor_pipeline/llm.py` already branches between Anthropic and
OpenRouter — both providers are served by this single adapter.
"""

from typing import Any, Sequence, Type, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel

from advisor_pipeline.llm import (
    get_llm,
    get_structured_output,
    invoke_text,
    invoke_vision,
)

T = TypeVar("T", bound=BaseModel)


class ChatLLMClient:
    """Satisfies `LLMClient` by delegating to `advisor_pipeline.llm` helpers."""

    def get_structured_output(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: str | None = None,
    ) -> T:
        return get_structured_output(schema, prompt, system_prompt)

    def invoke_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        return invoke_text(prompt, system_prompt)

    def invoke_vision(
        self,
        prompt: str,
        media_type: str,
        image_data: str,
    ) -> str:
        return invoke_vision(prompt, media_type, image_data)

    def bind_tools(self, tools: Sequence[Any]) -> BaseChatModel:
        return get_llm().bind_tools(tools)
