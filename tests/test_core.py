"""Unit and integration tests for Auto-Research core modules."""

import pytest
from auto_research.core.models import (
    ResearchObjective,
    ClaimEvidence,
    SearchDepth,
)
from auto_research.core.fact_matrix import FactMatrixManager
from auto_research.core.tree_search import TreeSearchEngine
from auto_research.core.critic import ResearchCritic
from auto_research.core.orchestrator import ResearchOrchestrator
from auto_research.tools.code_runner import PythonREPLTool


def test_fact_matrix_registration_and_deduplication():
    manager = FactMatrixManager()
    claim1 = ClaimEvidence(
        claim="Lithium dendrite growth degrades battery lifecycle.",
        evidence_quote="Experimental test shows dendrite formation reduces lifecycle by 40%.",
        source_url="https://example.com/paper1",
        source_title="Dendrite Study",
        confidence_score=0.9,
    )
    claim2 = ClaimEvidence(
        claim="Lithium dendrite growth degrades battery lifecycle.",
        evidence_quote="Another report on dendrites.",
        source_url="https://example.com/paper2",
        source_title="Study 2",
        confidence_score=0.95,
    )

    id1 = manager.register_claim(claim1)
    id2 = manager.register_claim(claim2)

    # Identical claim text should deduplicate to same ID and keep highest confidence
    assert id1 == id2
    claims = manager.get_all_claims()
    assert len(claims) == 1
    assert claims[0].confidence_score == 0.95


def test_tree_search_depth_governor():
    tree = TreeSearchEngine(max_depth=2, max_total_nodes=5)
    root = tree.add_root_node("Root Topic", ["query1"])
    assert root.depth_level == 0

    child1 = tree.spawn_child_node(root.id, "Child 1", ["child_query"])
    assert child1 is not None
    assert child1.depth_level == 1

    child2 = tree.spawn_child_node(child1.id, "Child 2", ["child2_query"])
    assert child2 is not None
    assert child2.depth_level == 2

    # Should be rejected by max_depth=2 cap
    child3 = tree.spawn_child_node(child2.id, "Child 3", ["child3_query"])
    assert child3 is None


@pytest.mark.asyncio
async def test_python_repl_tool():
    tool = PythonREPLTool()
    code = "import math\nprint(f'PI_ROUNDED={math.pi:.4f}')"
    res = await tool.execute(code)
    assert res.success is True
    assert "PI_ROUNDED=3.1416" in res.data["stdout"]


@pytest.mark.asyncio
async def test_orchestrator_end_to_end():
    objective = ResearchObjective(
        topic="AI Agent Context Compaction",
        target_questions=["How does microcompaction work?"],
        depth=SearchDepth.SHALLOW,
        max_rounds=2,
    )

    orchestrator = ResearchOrchestrator()
    report = await orchestrator.run(objective)

    assert report is not None
    assert "AI Agent Context Compaction" in report.title
    assert len(report.sections) > 0
    assert len(report.citations) > 0
    markdown_output = report.to_markdown()
    assert "# Autonomous Research Report" in markdown_output
    assert "## References & Citations" in markdown_output
