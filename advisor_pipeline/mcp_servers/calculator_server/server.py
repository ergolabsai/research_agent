# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
MCP Server for Mathematical and Scientific Calculations (HTTP/SSE Transport)

This server combines multiple tool modules:
- percentages: Percentage calculations
- basic_math: Arithmetic operations
- physics: Physics formulas

To add new tool categories, create a module in the tools/ directory.
"""

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
import uvicorn

from .tools.initialization import seed_formulas_if_empty
from .tools.mcp_tools import get_all_tools, handle_tool

# Ensure formula table exists and is seeded on import.
seed_formulas_if_empty()

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


# Create SSE transport
sse = SseServerTransport("/messages")


async def app(scope, receive, send):
    """Main ASGI application."""
    path = scope.get("path", "")
    method = scope.get("method", "GET")

    if path == "/health" and method == "GET":
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"status": "healthy", "server": "calculation-server"}',
        })

    elif path == "/sse" and method == "GET":
        async with sse.connect_sse(scope, receive, send) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options()
            )

    elif path == "/messages" and method == "POST":
        await sse.handle_post_message(scope, receive, send)

    else:
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"error": "Not found"}',
        })


if __name__ == "__main__":
    tools = get_all_tools()
    print(f"Starting MCP Calculation Server with {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}")
    print()
    print("Endpoints:")
    print("  SSE:      http://localhost:8000/sse")
    print("  Messages: http://localhost:8000/messages")
    print("  Health:   http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)