"""Shared LLM utilities replacing BaseAgent's dual-client pattern.

Provides a single LLM instance (Anthropic or OpenRouter) with helper methods for:
- Structured output via with_structured_output()
- Vision calls with image content blocks
- Simple text calls
"""

from typing import Type, TypeVar

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from advisor_pipeline.config.settings import settings

T = TypeVar("T", bound=BaseModel)


def _build_llm() -> BaseChatModel:
    """Build the LLM instance based on the configured provider."""
    if settings.llm_provider == "openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openrouter_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            timeout=settings.timeout_seconds,
        )
    else:
        return ChatAnthropic(
            model_name=settings.model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.anthropic_api_key,
            timeout=settings.timeout_seconds,
            stop=None,
        )


# Single shared LLM instance
_llm = _build_llm()


def get_llm() -> BaseChatModel:
    """Return the shared LLM instance."""
    return _llm


@retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=10))
def get_structured_output(schema: Type[T], prompt: str, system_prompt: str | None = None) -> T:
    """Get structured output from the LLM using with_structured_output().

    Args:
        schema: Pydantic model class to enforce on the response.
        prompt: The user prompt to send.
        system_prompt: Optional system prompt to prepend.

    Returns:
        Validated instance of *schema*.
    """
    structured_llm = _llm.with_structured_output(schema)
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))
    return structured_llm.invoke(messages)


@retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=10))
def invoke_vision(prompt_text: str, media_type: str, image_data: str) -> str:
    """Send an image + text prompt to the LLM via HumanMessage content blocks.

    Args:
        prompt_text: The text prompt to accompany the image.
        media_type: MIME type of the image (e.g. 'image/png').
        image_data: Base64-encoded image data.

    Returns:
        The LLM's text response.
    """
    message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{image_data}"},
            },
            {"type": "text", "text": prompt_text},
        ]
    )
    response = _llm.invoke([message])
    return response.content if isinstance(response.content, str) else str(response.content)


@retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=10))
def invoke_text(prompt_text: str, system_prompt: str | None = None) -> str:
    """Simple text call to the LLM.

    Args:
        prompt_text: The user prompt.
        system_prompt: Optional system prompt to prepend.

    Returns:
        The LLM's text response.
    """
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt_text))
    response = _llm.invoke(messages)
    return response.content if isinstance(response.content, str) else str(response.content)
