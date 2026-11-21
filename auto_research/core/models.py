"""Core Pydantic data models for the Auto-Research engine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchDepth(str, Enum):
    SHALLOW = "shallow"    # Fast survey (1-2 rounds)
    STANDARD = "standard"  # Standard exploration (3-5 rounds)
    DEEP = "deep"          # Exhaustive research with deep citation tracing (6-10 rounds)


class NodeStatus(str, Enum):
    PENDING = "pending"
    EXPLORING = "exploring"
    RESOLVED = "resolved"
    FAILED = "failed"
    PRUNED = "pruned"


class ResearchObjective(BaseModel):
    """The overarching research goal set by the user."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    topic: str
    target_questions: List[str] = Field(default_factory=list)
    depth: SearchDepth = SearchDepth.STANDARD
    max_rounds: int = 5
    max_tokens_budget: int = 200_000
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClaimEvidence(BaseModel):
    """Atomic factual claim extracted from a specific source."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    claim: str
    evidence_quote: str
    source_url: str
    source_title: str
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.9)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HypothesisNode(BaseModel):
    """A node in the research tree representing a sub-hypothesis or exploration path."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    question: str
    search_queries: List[str] = Field(default_factory=list)
    depth_level: int = 0
    priority_score: float = 1.0
    status: NodeStatus = NodeStatus.PENDING
    evidence_ids: List[str] = Field(default_factory=list)
    child_ids: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class FactMatrix(BaseModel):
    """Blackboard holding all extracted claims, indexed and grouped by topic."""
    claims: Dict[str, ClaimEvidence] = Field(default_factory=dict)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)

    def add_claim(self, claim: ClaimEvidence) -> None:
        self.claims[claim.id] = claim

    def get_claims_for_topic(self, keyword: str) -> List[ClaimEvidence]:
        kw = keyword.lower()
        return [
            c for c in self.claims.values()
            if kw in c.claim.lower() or kw in c.evidence_quote.lower()
        ]


class GapAnalysis(BaseModel):
    """Audit of missing information or weak arguments that need further exploration."""
    is_sufficient: bool
    missing_points: List[str] = Field(default_factory=list)
    suggested_queries: List[str] = Field(default_factory=list)
    confidence_ratio: float = 0.0


class Citation(BaseModel):
    """Validated citation linking a report statement directly to source evidence."""
    index: int
    source_title: str
    source_url: str
    exact_quote: str
    verified: bool = True


class ReportSection(BaseModel):
    """A single structured section of the generated research report."""
    title: str
    content: str
    citation_indices: List[int] = Field(default_factory=list)


class FinalReport(BaseModel):
    """The synthesized comprehensive research deliverable."""
    title: str
    objective: str
    executive_summary: str
    sections: List[ReportSection] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    total_sources_consulted: int = 0
    total_claims_verified: int = 0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_markdown(self) -> str:
        md = [f"# {self.title}\n", f"**Research Objective:** {self.objective}\n", f"**Date:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n", "---\n"]
        md.append("## Executive Summary\n")
        md.append(f"{self.executive_summary}\n\n")

        for section in self.sections:
            md.append(f"## {section.title}\n")
            md.append(f"{section.content}\n\n")

        if self.citations:
            md.append("---\n## References & Citations\n")
            for c in self.citations:
                md.append(f"[{c.index}] **{c.source_title}**  \nURL: {c.source_url}  \n> *\"{c.exact_quote}\"*\n\n")

        return "".join(md)
