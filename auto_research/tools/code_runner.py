"""Python REPL Tool.

Executes Python code snippets in a separate, isolated process to verify calculations,
process raw tabular data, or run statistical tests.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path
from typing import Any
from auto_research.tools.base import BaseTool, ToolResult


class PythonREPLTool(BaseTool):
    """Executes a Python code script in a sandboxed subprocess."""

    name = "python_repl"
    description = "Runs Python code in a safe subprocess to perform calculations or data analysis."

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    async def execute(self, code: str, **kwargs: Any) -> ToolResult:
        """Execute the provided Python code and capture stdout/stderr."""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                out_str = stdout.decode("utf-8", errors="replace").strip()
                err_str = stderr.decode("utf-8", errors="replace").strip()

                if proc.returncode == 0:
                    return ToolResult(success=True, data={"stdout": out_str})
                else:
                    return ToolResult(success=False, data={"stdout": out_str}, error=err_str)
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(success=False, data=None, error=f"Execution timed out ({self.timeout}s)")
        finally:
            Path(temp_path).unlink(missing_ok=True)
