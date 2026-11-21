"""Research Critic and Anti-Hallucination Verifier.

Performs gap analysis (identifying missing evidence) and verifies citation integrity
to prevent hallucinations in generated reports.
"""

from __future__ import annotations

from typing import List, Tuple
from auto_research.core.models import (
    Citation,
    ClaimEvidence,
    GapAnalysis,
    ReportSection,
    ResearchObjective,
)
from auto_research.core.fact_matrix import FactMatrixManager


class ResearchCritic:
    """Auditor ensuring high evidentiary standards and absence of fabricated citations."""

    def __init__(self, fact_manager: FactMatrixManager) -> None:
        self.fact_manager = fact_manager

    def perform_gap_analysis(
        self,
        objective: ResearchObjective,
        current_claims: List[ClaimEvidence],
    ) -> GapAnalysis:
        """Inspect if current collected claims sufficiently answer the objective's target questions."""
        if not objective.target_questions:
            # If no explicit sub-questions provided, use general depth metric
            is_suff = len(current_claims) >= (objective.max_rounds * 2)
            ratio = min(1.0, len(current_claims) / max(1, objective.max_rounds * 2))
            return GapAnalysis(
                is_sufficient=is_suff,
                missing_points=[] if is_suff else [f"Need more evidence on: {objective.topic}"],
                suggested_queries=[f"{objective.topic} technical details", f"{objective.topic} analysis"] if not is_suff else [],
                confidence_ratio=ratio,
            )

        missing = []
        suggested = []
        answered_count = 0

        for question in objective.target_questions:
            kw_tokens = [w.lower() for w in question.split() if len(w) > 3]
            matched = False
            for claim in current_claims:
                text = (claim.claim + " " + claim.evidence_quote).lower()
                matches = sum(1 for tok in kw_tokens if tok in text)
                if matches >= min(2, len(kw_tokens)):
                    matched = True
                    break

            if matched:
                answered_count += 1
            else:
                missing.append(question)
                suggested.append(f"research on: {question}")

        ratio = answered_count / len(objective.target_questions)
        is_sufficient = (ratio >= 0.75) or (len(missing) == 0)

        return GapAnalysis(
            is_sufficient=is_sufficient,
            missing_points=missing,
            suggested_queries=suggested,
            confidence_ratio=ratio,
        )

    def verify_citations(
        self,
        sections: List[ReportSection],
        citations: List[Citation],
    ) -> Tuple[bool, List[str]]:
        """Verify that every citation index corresponds to real, non-hallucinated source evidence."""
        registered_citations = {c.index: c for c in citations}
        stored_claims = {c.id: c for c in self.fact_manager.get_all_claims()}
        issues = []

        for section in sections:
            for idx in section.citation_indices:
                if idx not in registered_citations:
                    issues.append(f"Section '{section.title}' references non-existent citation [{idx}].")
                    continue

                cit = registered_citations[idx]
                # Check if citation quote exists in stored claims
                matched_source = False
                for claim in stored_claims.values():
                    if claim.source_url == cit.source_url:
                        # Check substring overlap
                        if cit.exact_quote[:30].lower() in claim.evidence_quote.lower():
                            matched_source = True
                            break

                if not matched_source:
                    # In strict mode, flags citations without proof
                    cit.verified = False
                    issues.append(f"Citation [{idx}] '{cit.source_title}' lacks verified quote in evidence matrix.")

        all_valid = len(issues) == 0
        return all_valid, issues
