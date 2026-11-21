"""Main Research Orchestrator.

Implements the multi-agent closed loop:
Objective -> Hypothesis Breakdown -> Search & Crawl -> Fact Matrix Extraction
-> Gap Analysis -> Tree Expansion -> Citation Verification -> Final Report.
"""

from __future__ import annotations

import asyncio
from typing import Callable, List, Optional
from auto_research.core.models import (
    ClaimEvidence,
    FinalReport,
    ResearchObjective,
)
from auto_research.core.fact_matrix import FactMatrixManager
from auto_research.core.tree_search import TreeSearchEngine
from auto_research.core.critic import ResearchCritic
from auto_research.tools.search_tool import WebSearchTool
from auto_research.tools.crawler_tool import WebCrawlerTool
from auto_research.synthesizer.report_generator import ReportGenerator


class ResearchOrchestrator:
    """Coordinates the entire deep research process."""

    def __init__(
        self,
        search_tool: Optional[WebSearchTool] = None,
        crawler_tool: Optional[WebCrawlerTool] = None,
        max_depth: int = 3,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.search_tool = search_tool or WebSearchTool()
        self.crawler_tool = crawler_tool or WebCrawlerTool()
        self.fact_manager = FactMatrixManager()
        self.tree_search = TreeSearchEngine(max_depth=max_depth)
        self.critic = ResearchCritic(self.fact_manager)
        self.report_generator = ReportGenerator(self.fact_manager)
        self.on_progress = on_progress or (lambda msg: None)

    async def run(self, objective: ResearchObjective) -> FinalReport:
        """Execute the end-to-end autonomous research workflow."""
        self.on_progress(f"🎯 Initiating deep research on: '{objective.topic}'")

        # 1. Initialize root node
        initial_queries = [objective.topic] + [f"{objective.topic} {q}" for q in objective.target_questions[:2]]
        root = self.tree_search.add_root_node(
            question=f"Core investigation of {objective.topic}",
            search_queries=initial_queries,
        )

        rounds_completed = 0
        max_rounds = objective.max_rounds

        # 2. Main Agentic Research Loop
        while self.tree_search.has_pending_nodes() and rounds_completed < max_rounds:
            node = self.tree_search.pop_next_node()
            if not node:
                break

            rounds_completed += 1
            self.on_progress(f"🔍 [Round {rounds_completed}/{max_rounds}] Exploring node: '{node.question}' (depth: {node.depth_level})")

            collected_claims_for_node: List[str] = []

            # Execute searches for this node's queries
            for query in node.search_queries[:2]:
                self.on_progress(f"   ↳ Querying: '{query}'")
                search_res = await self.search_tool.execute(query=query, max_results=3)

                if not search_res.success or not search_res.data:
                    continue

                # Crawl candidate URLs
                for item in search_res.data[:2]:
                    url = item.get("url")
                    title = item.get("title", "Resource")
                    snippet = item.get("snippet", "")

                    if not url:
                        continue

                    # Register baseline claim from search snippet
                    claim_id = self.fact_manager.register_claim(
                        ClaimEvidence(
                            claim=snippet[:120],
                            evidence_quote=snippet,
                            source_url=url,
                            source_title=title,
                            confidence_score=0.85,
                        )
                    )
                    collected_claims_for_node.append(claim_id)

                    # Crawl page for deeper extraction
                    crawl_res = await self.crawler_tool.execute(url=url)
                    if crawl_res.success and crawl_res.data:
                        page_text = crawl_res.data.get("text", "")
                        # Simple high-signal paragraph extraction
                        paragraphs = [p.strip() for p in page_text.split("\n") if len(p.strip()) > 80]
                        for p in paragraphs[:2]:
                            deep_claim_id = self.fact_manager.register_claim(
                                ClaimEvidence(
                                    claim=p[:100] + "...",
                                    evidence_quote=p[:300],
                                    source_url=url,
                                    source_title=title,
                                    confidence_score=0.92,
                                )
                            )
                            collected_claims_for_node.append(deep_claim_id)

            # Mark node resolved
            node_summary = f"Identified {len(collected_claims_for_node)} evidentiary findings regarding {node.question}."
            self.tree_search.mark_node_resolved(node.id, summary=node_summary, evidence_ids=collected_claims_for_node)

            # 3. Gap Analysis & Dynamic Tree Expansion
            gap_analysis = self.critic.perform_gap_analysis(objective, self.fact_manager.get_all_claims())
            if not gap_analysis.is_sufficient and gap_analysis.suggested_queries:
                for q in gap_analysis.suggested_queries[:2]:
                    child = self.tree_search.spawn_child_node(
                        parent_id=node.id,
                        question=f"Deeper investigation into {q}",
                        search_queries=[q],
                        priority_score=0.75,
                    )
                    if child:
                        self.on_progress(f"   🌱 Spawned child research branch: '{child.question}'")

        self.on_progress(f"📊 Research loop converged. Total claims in FactMatrix: {len(self.fact_manager.get_all_claims())}")
        self.on_progress("📝 Synthesizing comprehensive research deliverable...")

        # 4. Generate Final Report
        resolved_nodes = self.tree_search.get_all_resolved_nodes()
        report = self.report_generator.generate_report(objective, resolved_nodes)

        # 5. Double-blind Citation Verification
        is_valid, audit_issues = self.critic.verify_citations(report.sections, report.citations)
        if not is_valid:
            self.on_progress(f"⚠️ Citation verification warning: {len(audit_issues)} issues flagged.")
        else:
            self.on_progress("✅ All citations strictly verified against FactMatrix evidence.")

        return report
