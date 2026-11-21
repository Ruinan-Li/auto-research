"""Command-Line Interface (CLI) for Auto-Research.

Provides an interactive, beautiful terminal experience with Rich formatting,
live progress reporting, and output saving.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from auto_research.core.models import ResearchObjective, SearchDepth
from auto_research.core.orchestrator import ResearchOrchestrator


console = Console()


async def run_cli_research(topic: str, questions: list[str], rounds: int, output_file: str | None) -> None:
    """Run research via CLI with rich console output."""
    console.print(
        Panel.fit(
            "[bold cyan]Auto-Research Agent[/bold cyan]\n"
            "[dim]Industrial-Grade Autonomous Deep Research Engine[/dim]",
            border_style="cyan",
        )
    )

    objective = ResearchObjective(
        topic=topic,
        target_questions=questions,
        depth=SearchDepth.STANDARD,
        max_rounds=rounds,
    )

    console.print(f"[bold green]Target Topic:[/bold green] {topic}")
    if questions:
        console.print("[bold yellow]Sub-questions:[/bold yellow]")
        for q in questions:
            console.print(f"  • {q}")
    console.print(f"[bold blue]Max Exploration Rounds:[/bold blue] {rounds}\n")

    def progress_callback(msg: str) -> None:
        console.print(f"[dim cyan]{msg}[/dim cyan]")

    orchestrator = ResearchOrchestrator(on_progress=progress_callback)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Conducting deep research...", total=None)
        report = await orchestrator.run(objective)
        progress.update(task, completed=True)

    console.print("\n[bold green]✨ Research Completed Successfully![/bold green]\n")
    console.print(Panel(Markdown(report.to_markdown()), title=report.title, border_style="green"))

    # Save to file
    out_path = Path(output_file or f"research_report_{objective.id}.md")
    out_path.write_text(report.to_markdown(), encoding="utf-8")
    console.print(f"\n📁 Report saved to: [bold underline]{out_path.resolve()}[/bold underline]")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Auto-Research: Autonomous Deep Research Engine")
    parser.add_argument("topic", nargs="?", help="Research topic or question to investigate")
    parser.add_argument("-q", "--questions", nargs="+", default=[], help="Specific target sub-questions")
    parser.add_argument("-r", "--rounds", type=int, default=4, help="Maximum research tree rounds (default: 4)")
    parser.add_argument("-o", "--output", help="Output file path (default: research_report_<id>.md)")

    args = parser.parse_args()

    topic = args.topic
    if not topic:
        console.print("[bold yellow]Enter research topic / goal:[/bold yellow] ", end="")
        topic = input().strip()
        if not topic:
            console.print("[red]Topic cannot be empty. Exiting.[/red]")
            sys.exit(1)

    asyncio.run(run_cli_research(topic, args.questions, args.rounds, args.output))


if __name__ == "__main__":
    main()
