"""Quickstart example demonstrating Auto-Research in code."""

import asyncio
from auto_research.core.models import ResearchObjective, SearchDepth
from auto_research.core.orchestrator import ResearchOrchestrator


async def main():
    objective = ResearchObjective(
        topic="Solid-State Battery Commercialization Barriers",
        target_questions=[
            "What are the primary ionic conductivity bottlenecks at room temperature?",
            "How does interfacial resistance compare between sulfide and oxide electrolytes?",
            "What is the projected cost per kWh parity timeline with lithium-ion?",
        ],
        depth=SearchDepth.STANDARD,
        max_rounds=3,
    )

    def print_progress(msg: str):
        print(f"[PROGRESS] {msg}")

    orchestrator = ResearchOrchestrator(on_progress=print_progress)
    report = await orchestrator.run(objective)

    print("\n" + "=" * 60)
    print(report.to_markdown())
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
