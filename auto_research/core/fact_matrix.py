"""Fact Matrix (Blackboard) knowledge store.

Implements the blackboard pattern: manages atomic claims, detects potential
contradictions between opposing sources, and provides structured evidence querying.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple
from auto_research.core.models import ClaimEvidence, FactMatrix


class FactMatrixManager:
    """Manages the FactMatrix blackboard during research."""

    def __init__(self) -> None:
        self.matrix = FactMatrix()
        self._url_index: Dict[str, List[str]] = {}

    def register_claim(self, claim: ClaimEvidence) -> str:
        """Register a new atomic claim with deduplication check."""
        # Simple fingerprinting check to avoid identical claims
        norm_claim = self._normalize_text(claim.claim)
        for existing_id, existing in self.matrix.claims.items():
            if self._normalize_text(existing.claim) == norm_claim:
                # Merge source or keep higher confidence
                if claim.confidence_score > existing.confidence_score:
                    self.matrix.claims[existing_id] = claim
                return existing_id

        self.matrix.add_claim(claim)
        self._url_index.setdefault(claim.source_url, []).append(claim.id)
        return claim.id

    def get_all_claims(self) -> List[ClaimEvidence]:
        """Return all claims stored in the matrix."""
        return list(self.matrix.claims.values())

    def get_claims_by_ids(self, claim_ids: List[str]) -> List[ClaimEvidence]:
        """Fetch specific claims by their IDs."""
        return [self.matrix.claims[cid] for cid in claim_ids if cid in self.matrix.claims]

    def find_contradictions(self) -> List[Tuple[ClaimEvidence, ClaimEvidence, str]]:
        """Identify potential factual contradictions between claims from different sources."""
        claims_list = list(self.matrix.claims.values())
        contradictions = []

        # Simple negation / conflict heuristics
        negation_markers = ["not", "failed", "no evidence", "unsupported", "contrary", "false", "disproved", "decrease", "decline"]
        positive_markers = ["effective", "proven", "succeeded", "significant", "increase", "growth", "breakthrough"]

        for i in range(len(claims_list)):
            for j in range(i + 1, len(claims_list)):
                c1, c2 = claims_list[i], claims_list[j]
                if c1.source_url == c2.source_url:
                    continue  # Same source unlikely to directly contradict self without nuance

                t1, t2 = c1.claim.lower(), c2.claim.lower()
                # Check overlapping keywords
                words1 = set(re.findall(r"\w+", t1))
                words2 = set(re.findall(r"\w+", t2))
                overlap = words1.intersection(words2)

                # If discussing the same subject with opposing markers
                if len(overlap) >= 3:
                    c1_has_neg = any(m in t1 for m in negation_markers)
                    c2_has_neg = any(m in t2 for m in negation_markers)
                    c1_has_pos = any(m in t1 for m in positive_markers)
                    c2_has_pos = any(m in t2 for m in positive_markers)

                    if (c1_has_pos and c2_has_neg) or (c1_has_neg and c2_has_pos):
                        reason = f"Conflicting assertion between '{c1.source_title}' and '{c2.source_title}'"
                        contradictions.append((c1, c2, reason))

        return contradictions

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(re.findall(r"\w+", text.lower()))
