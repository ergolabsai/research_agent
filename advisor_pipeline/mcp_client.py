"""Thin sync wrapper around the MCP SDK for the calculator server.

Runs the async MCP ClientSession in a background thread so that
MathEvaluator's sync tool functions (called inside LangGraph's
create_react_agent) can call MCP tools without event-loop conflicts.
"""

import json
import sys
import threading
import asyncio
from concurrent.futures import Future
from contextlib import asynccontextmanager

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.sse import sse_client

from advisor_pipeline.config.settings import settings


class CalculatorClient:
    """Sync MCP client that bridges to an async ClientSession in a background thread."""

    def __init__(self, transport: str | None = None):
        self._transport = transport or settings.calculator_transport
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._session: ClientSession | None = None
        self._ready = threading.Event()
        self._shutdown = asyncio.Event()
        self._error: Exception | None = None

    # ------------------------------------------------------------------
    # Async internals
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def _open_transport(self):
        """Yield (read_stream, write_stream) for the configured transport."""
        if self._transport == "stdio":
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "advisor_pipeline.mcp_servers.calculator_server.server_stdio"],
            )
            async with stdio_client(server_params) as streams:
                yield streams
        elif self._transport == "sse":
            url = settings.mcp_server_url or "http://localhost:8000/sse"
            async with sse_client(url) as streams:
                yield streams
        else:
            raise ValueError(f"Unknown transport: {self._transport!r}  (expected 'stdio' or 'sse')")

    async def _run(self):
        """Main coroutine that lives in the background thread."""
        try:
            async with self._open_transport() as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    self._session = session
                    self._ready.set()
                    # Block until close() signals shutdown
                    await self._shutdown.wait()
        except Exception as exc:
            self._error = exc
            self._ready.set()  # unblock connect() so it can raise

    def _thread_target(self):
        """Entry point for the background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._run())

    # ------------------------------------------------------------------
    # Public sync API
    # ------------------------------------------------------------------

    def connect(self):
        """Start the background thread and wait for the MCP session to be ready."""
        self._thread = threading.Thread(target=self._thread_target, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=30)
        if self._error:
            raise self._error
        if self._session is None:
            raise RuntimeError("MCP session failed to initialize")

    def call_tool(self, name: str, **kwargs) -> dict:
        """Call an MCP tool synchronously. Returns parsed JSON result."""
        if self._session is None or self._loop is None:
            raise RuntimeError("Client not connected — call connect() first")

        future: Future = asyncio.run_coroutine_threadsafe(
            self._session.call_tool(name, arguments=kwargs if kwargs else None),
            self._loop,
        )
        result = future.result(timeout=30)
        # CallToolResult.content is a list; first item is typically TextContent
        text = result.content[0].text
        return json.loads(text)

    def close(self):
        """Tear down the MCP session and background thread."""
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._shutdown.set)
        if self._thread:
            self._thread.join(timeout=10)
        self._session = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.close()
