"""BaseTool abstraction and execution contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Encapsulates the standard output of a tool call."""
    success: bool
    data: Any
    error: str | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all research tools."""

    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool asynchronously and return a structured ToolResult."""
        pass
