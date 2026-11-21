"""Tree Search Engine with depth & budget governor.

Manages exploration branches, prioritizes high-value sub-questions, and enforces
depth caps to prevent infinite loops.
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Optional
from auto_research.core.models import HypothesisNode, NodeStatus


class TreeSearchEngine:
    """Exploration frontier manager implementing heuristic priority tree search."""

    def __init__(self, max_depth: int = 4, max_total_nodes: int = 30) -> None:
        self.max_depth = max_depth
        self.max_total_nodes = max_total_nodes
        self.nodes: Dict[str, HypothesisNode] = {}
        # Priority queue stores (-priority_score, node_id)
        self._frontier: List[tuple[float, str]] = []

    def add_root_node(self, question: str, search_queries: List[str]) -> HypothesisNode:
        """Create and register the root research node."""
        root = HypothesisNode(
            question=question,
            search_queries=search_queries,
            depth_level=0,
            priority_score=1.0,
            status=NodeStatus.PENDING,
        )
        self.nodes[root.id] = root
        heapq.heappush(self._frontier, (-root.priority_score, root.id))
        return root

    def spawn_child_node(
        self,
        parent_id: str,
        question: str,
        search_queries: List[str],
        priority_score: float = 0.8,
    ) -> Optional[HypothesisNode]:
        """Spawn a child exploration node if depth and total node budget permit."""
        parent = self.nodes.get(parent_id)
        if not parent:
            return None

        new_depth = parent.depth_level + 1
        if new_depth > self.max_depth or len(self.nodes) >= self.max_total_nodes:
            # Depth governor or budget cap reached
            return None

        child = HypothesisNode(
            parent_id=parent_id,
            question=question,
            search_queries=search_queries,
            depth_level=new_depth,
            priority_score=priority_score,
            status=NodeStatus.PENDING,
        )
        self.nodes[child.id] = child
        parent.child_ids.append(child.id)
        heapq.heappush(self._frontier, (-child.priority_score, child.id))
        return child

    def pop_next_node(self) -> Optional[HypothesisNode]:
        """Pop the highest priority pending node from the frontier."""
        while self._frontier:
            _, node_id = heapq.heappop(self._frontier)
            node = self.nodes.get(node_id)
            if node and node.status == NodeStatus.PENDING:
                node.status = NodeStatus.EXPLORING
                return node
        return None

    def mark_node_resolved(self, node_id: str, summary: str, evidence_ids: List[str]) -> None:
        """Mark a node as successfully resolved with collected evidence."""
        node = self.nodes.get(node_id)
        if node:
            node.status = NodeStatus.RESOLVED
            node.summary = summary
            node.evidence_ids.extend(evidence_ids)

    def mark_node_failed(self, node_id: str) -> None:
        """Mark a node as failed or unanswerable."""
        node = self.nodes.get(node_id)
        if node:
            node.status = NodeStatus.FAILED

    def has_pending_nodes(self) -> bool:
        """Check if any nodes remain to be explored."""
        return any(n.status == NodeStatus.PENDING for n in self.nodes.values())

    def get_all_resolved_nodes(self) -> List[HypothesisNode]:
        """Return all successfully explored and resolved nodes."""
        return [n for n in self.nodes.values() if n.status == NodeStatus.RESOLVED]
