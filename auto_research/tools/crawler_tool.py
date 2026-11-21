"""Web Crawler and High-Signal Content Extractor.

Fetches web pages, strips HTML noise (boilerplate, nav, scripts), and returns clean,
readable paragraphs suitable for claim extraction.
"""

from __future__ import annotations

import re
from typing import Any
import httpx
from auto_research.tools.base import BaseTool, ToolResult


class WebCrawlerTool(BaseTool):
    """Fetches a URL and extracts clean, high-signal text content."""

    name = "web_crawler"
    description = "Downloads a webpage and extracts clean, readable text."

    def __init__(self, timeout: float = 12.0) -> None:
        self.timeout = timeout

    async def execute(self, url: str, **kwargs: Any) -> ToolResult:
        """Fetch and clean the target URL content."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"HTTP {resp.status_code} error fetching {url}",
                    )

                text = self._clean_html(resp.text)
                return ToolResult(
                    success=True,
                    data={
                        "url": str(resp.url),
                        "text": text[:15000],  # Token budget guard per page
                        "length": len(text),
                    },
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to crawl {url}: {e}",
            )

    @staticmethod
    def _clean_html(html_content: str) -> str:
        """Strip HTML tags, scripts, styles, and collapse redundant whitespace."""
        # Remove script and style elements
        clean = re.sub(r"<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>", " ", html_content, flags=re.DOTALL | re.IGNORECASE)
        # Strip all HTML tags
        clean = re.sub(r"<[^>]+>", " ", clean)
        # Unescape common entities
        clean = clean.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
        # Collapse multiple whitespace/newlines
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean
