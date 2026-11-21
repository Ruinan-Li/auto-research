"""MCP (Model Context Protocol) Client Integration.

Enables the Auto-Research agent to dynamically connect to standard MCP servers
(e.g., arXiv MCP, Database MCP, GitHub MCP) via standard JSON-RPC 2.0 over stdio.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional
from auto_research.tools.base import BaseTool, ToolResult


class MCPToolClient(BaseTool):
    """Wraps an external MCP Server accessed via stdio JSON-RPC 2.0."""

    name = "mcp_tool"
    description = "Dispatches tool execution to an external MCP Server via JSON-RPC over stdio."

    def __init__(self, command: str, args: List[str]) -> None:
        self.command = command
        self.args = args
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._msg_id = 0

    async def start(self) -> None:
        """Start the MCP server subprocess."""
        self._proc = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Query the MCP server for its advertised tools (tools/list)."""
        response = await self._send_request("tools/list", {})
        return response.get("tools", [])

    async def execute(self, tool_name: str, arguments: Dict[str, Any], **kwargs: Any) -> ToolResult:
        """Call an MCP tool on the server (tools/call)."""
        if not self._proc:
            await self.start()

        try:
            result = await self._send_request(
                "tools/call",
                {"name": tool_name, "arguments": arguments},
            )
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"MCP call failed: {e}")

    async def close(self) -> None:
        """Terminate the MCP server process."""
        if self._proc:
            try:
                self._proc.terminate()
                await self._proc.wait()
            except Exception:
                pass
            self._proc = None

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC 2.0 request over stdin and await response from stdout."""
        if not self._proc or not self._proc.stdin or not self._proc.stdout:
            raise RuntimeError("MCP process is not running")

        self._msg_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self._msg_id,
            "method": method,
            "params": params,
        }

        payload = (json.dumps(req) + "\n").encode("utf-8")
        self._proc.stdin.write(payload)
        await self._proc.stdin.drain()

        # Read line from stdout
        line = await self._proc.stdout.readline()
        if not line:
            raise RuntimeError("MCP server closed stream unexpectedly")

        resp = json.loads(line.decode("utf-8"))
        if "error" in resp:
            raise RuntimeError(f"MCP error: {resp['error']}")

        return resp.get("result", {})
