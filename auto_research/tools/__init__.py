"""Tooling interface and implementations for the Auto-Research engine."""

from auto_research.tools.base import BaseTool, ToolResult
from auto_research.tools.search_tool import WebSearchTool
from auto_research.tools.crawler_tool import WebCrawlerTool
from auto_research.tools.code_runner import PythonREPLTool
from auto_research.tools.mcp_client import MCPToolClient

__all__ = [
    "BaseTool",
    "ToolResult",
    "WebSearchTool",
    "WebCrawlerTool",
    "PythonREPLTool",
    "MCPToolClient",
]
