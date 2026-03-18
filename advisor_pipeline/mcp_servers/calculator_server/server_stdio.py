#!/usr/bin/env python3
"""
MCP Server for Mathematical and Scientific Calculations (Stdio Transport)

This server combines multiple tool modules:
- percentages: Percentage calculations
- basic_math: Arithmetic operations
- physics: Physics formulas

Use this version for Claude Desktop integration.
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.initialization import seed_formulas_if_empty
from .tools.mcp_tools import get_all_tools, handle_tool

# Create the MCP server
server = Server("calculation-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools from all modules."""
    return get_all_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to the appropriate module."""
    return await handle_tool(name, arguments)


async def main():
    seed_formulas_if_empty()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())