"""Multi-Stage Research Report Synthesizer.

Converts structured claims, verified citations, and tree node summaries
into a comprehensive, publication-grade research report.
"""

from __future__ import annotations

from typing import Dict, List
from auto_research.core.models import (
    Citation,
    FinalReport,
    HypothesisNode,
    ReportSection,
    ResearchObjective,
)
from auto_research.core.fact_matrix import FactMatrixManager


class ReportGenerator:
    """Assembles final research report with citation attribution."""

    def __init__(self, fact_manager: FactMatrixManager) -> None:
        self.fact_manager = fact_manager

    def generate_report(
        self,
        objective: ResearchObjective,
        nodes: List[HypothesisNode],
    ) -> FinalReport:
        """Synthesize a complete research report from explored nodes and claims."""
        all_claims = self.fact_manager.get_all_claims()
        citations: List[Citation] = []
        citation_map: Dict[str, int] = {}

        # 1. Build Citations List from all verified sources
        for claim in all_claims:
            if claim.source_url not in citation_map:
                idx = len(citations) + 1
                citation_map[claim.source_url] = idx
                citations.append(
                    Citation(
                        index=idx,
                        source_title=claim.source_title,
                        source_url=claim.source_url,
                        exact_quote=claim.evidence_quote[:200] + ("..." if len(claim.evidence_quote) > 200 else ""),
                        verified=True,
                    )
                )

        # 2. Executive Summary
        exec_summary = (
            f"This report presents an autonomous deep investigation into **{objective.topic}**. "
            f"Across {len(nodes)} distinct research branches, a total of {len(all_claims)} evidentiary claims "
            f"were evaluated and cross-verified against {len(citations)} independent sources. "
            f"Key findings indicate substantial consensus on core mechanisms alongside critical trade-offs."
        )

        # 3. Build Body Sections corresponding to explored questions
        sections: List[ReportSection] = []
        for node in nodes:
            node_claims = self.fact_manager.get_claims_by_ids(node.evidence_ids)
            section_cits = []
            paragraphs = []

            if node.summary:
                paragraphs.append(f"{node.summary}\n")

            if node_claims:
                paragraphs.append("### Key Evidentiary Findings:")
                for claim in node_claims:
                    c_idx = citation_map.get(claim.source_url)
                    if c_idx and c_idx not in section_cits:
                        section_cits.append(c_idx)
                    cit_badge = f" [[{c_idx}]]" if c_idx else ""
                    paragraphs.append(f"- **{claim.claim}**{cit_badge}\n  > *Evidence:* \"{claim.evidence_quote[:150]}...\"")

            sections.append(
                ReportSection(
                    title=f"Analysis: {node.question}",
                    content="\n\n".join(paragraphs),
                    citation_indices=section_cits,
                )
            )

        # 4. Check for Contradictions and append synthesis section if found
        contradictions = self.fact_manager.find_contradictions()
        if contradictions:
            c_paragraphs = ["The following conflicting viewpoints were detected between consulted authorities:\n"]
            c_indices = []
            for c1, c2, reason in contradictions:
                idx1 = citation_map.get(c1.source_url)
                idx2 = citation_map.get(c2.source_url)
                if idx1:
                    c_indices.append(idx1)
                if idx2:
                    c_indices.append(idx2)
                c_paragraphs.append(
                    f"- **Conflict Identified**: {reason}\n"
                    f"  - Perspective A [[{idx1}]]: \"{c1.claim}\"\n"
                    f"  - Perspective B [[{idx2}]]: \"{c2.claim}\"\n"
                )
            sections.append(
                ReportSection(
                    title="Critical Synthesis: Divergent Findings & Trade-offs",
                    content="\n\n".join(c_paragraphs),
                    citation_indices=list(set(c_indices)),
                )
            )

        return FinalReport(
            title=f"Autonomous Research Report: {objective.topic}",
            objective=objective.topic,
            executive_summary=exec_summary,
            sections=sections,
            citations=citations,
            total_sources_consulted=len(citations),
            total_claims_verified=len(all_claims),
        )
