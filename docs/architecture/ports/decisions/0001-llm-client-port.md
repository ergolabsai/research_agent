---
id: ports-0001
title: `LLMClient` port for text and vision model calls
status: accepted
date: 2026-05-17
supersedes: []
superseded-by: []
---

## Context

Every LLM-using service in the system (the orchestrator, the figure evaluator, the math evaluator, the librarian) calls a chat-style model. Today the calls go through a single shared `ChatAnthropic` instance imported from a module-level global. The benefits of having a single chokepoint are real, but the choke is too low-level: every caller depends on the Anthropic SDK's class directly, with retry behavior glued on with decorators.

The system must support at least:

- Switching providers (Anthropic ↔ OpenRouter ↔ local model) without touching agent code.
- Text and vision modalities.
- Structured output (Pydantic-validated responses).
- Retries with backoff (configured once, applied uniformly).

A port is the natural way to surface these.

## Decision

Declare an `LLMClient` port:

```python
class LLMClient(Protocol):
    async def invoke_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str: ...

    async def invoke_vision(
        self,
        prompt: str,
        images: Sequence[ImagePayload],
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str: ...

    async def get_structured_output(
        self,
        schema: type[T],
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
    ) -> T: ...
```

`ImagePayload` is a contract type carrying `data: str` (base64) and `media_type: str`. `T` is a `BaseModel` subclass.

The port handles retries internally (the adapter wraps each call in the standard `tenacity` policy). Callers do not configure retries.

Per-call `model=` is optional; if omitted, the adapter uses its default (read from config at construction).

## Consequences

**Easy:**
- Every LLM call in the system goes through one interface. Telemetry, tracing, and rate-limiting hooks have a single insertion point.
- Provider swaps are a composition-layer change: replace `AnthropicLLMClient` with `OpenRouterLLMClient`. Use-cases and services do not change.
- Test adapters return canned responses; tests are deterministic and fast.

**Hard:**
- The port must serve every realistic LLM use case in the system. Three methods cover today's needs (text, vision, structured output); a future capability (streaming, tool use within a single call) may require port evolution.
- "Structured output" can be implemented via different mechanisms by different providers (Anthropic's tool-use, OpenAI's JSON mode, Instructor library). The port hides this; the adapter chooses.

**Forecloses:**
- Direct imports of `anthropic` or `openai` or `langchain.chat_models` from anywhere outside `adapters/driven/llm/`.
- Per-caller retry policies. Retries are a property of the adapter.

## Adapters

- **`AnthropicLLMClient`** — current default. Wraps `ChatAnthropic` from `langchain-anthropic`, with `@retry` for stop_after_attempt(3) + exponential backoff.
- **`OpenRouterLLMClient`** — switchable. Same interface, different base URL and auth.
- **`FakeLLMClient`** — test-only. Returns programmed responses for specific prompt patterns.

See [adapters/driven/decisions/0001-anthropic-llm-adapter.md](../../adapters/driven/decisions/0001-anthropic-llm-adapter.md).

## Review trigger

- A use-case needs streaming responses (token-by-token) that cannot be expressed as a single `await`. Add a `stream(...)` method to the port — evolve, do not bypass.
- A new modality enters the system (audio in/out, embeddings as a primary call). Embeddings are likely a *separate* port (`Embedder`) rather than a method on `LLMClient`, because the consumer pattern differs.
- Tool-use becomes a first-class feature inside agent calls (LLM calls a tool, gets a result, continues). At that point the port may need a `with_tools(...)` variant or the agent loop moves to a different abstraction.
