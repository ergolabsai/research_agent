# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""MCP Advisor Server — stdio transport.

Registers prompt templates and tools for the Advisor pipeline.
Run with:  python -m advisor_pipeline.mcp_servers.advisor_server.server
"""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import GetPromptResult, Prompt, PromptArgument, PromptMessage, TextContent, Tool

from advisor_pipeline.mcp_servers.advisor_server.prompts import PROMPT_REGISTRY
from advisor_pipeline.mcp_servers.advisor_server.tools import get_all_tools, handle_tool

server = Server("advisor-server")


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    prompts = []
    for name, template in PROMPT_REGISTRY.items():
        # Extract {placeholders} from the template string
        import re
        placeholders = re.findall(r"\{(\w+)\}", template)
        args = [
            PromptArgument(name=p, description=f"Value for {p}", required=True)
            for p in sorted(set(placeholders))
        ]
        prompts.append(Prompt(name=name, description=f"Prompt template: {name}", arguments=args))
    return prompts


@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
    template = PROMPT_REGISTRY.get(name)
    if template is None:
        raise ValueError(f"Unknown prompt: {name}")
    text = template.format(**(arguments or {}))
    return GetPromptResult(
        description=f"Rendered prompt: {name}",
        messages=[PromptMessage(role="user", content=TextContent(type="text", text=text))],
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[Tool]:
    return get_all_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    return await handle_tool(name, arguments)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
