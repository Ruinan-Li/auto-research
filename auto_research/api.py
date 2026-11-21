"""FastAPI Web Server for Auto-Research.

Provides HTTP REST endpoints for queuing research jobs and retrieving reports.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from auto_research.core.models import ResearchObjective, FinalReport, SearchDepth
from auto_research.core.orchestrator import ResearchOrchestrator


app = FastAPI(
    title="Auto-Research API",
    description="Industrial-Grade Autonomous Deep Research Engine",
    version="0.1.0",
)

# In-memory storage for jobs
jobs_db: Dict[str, Dict[str, object]] = {}


class CreateResearchRequest(BaseModel):
    topic: str
    target_questions: List[str] = Field(default_factory=list)
    depth: SearchDepth = SearchDepth.STANDARD
    max_rounds: int = 4


@app.post("/api/research", response_model=Dict[str, str])
async def create_research_job(req: CreateResearchRequest):
    """Start an autonomous research job in the background."""
    objective = ResearchObjective(
        topic=req.topic,
        target_questions=req.target_questions,
        depth=req.depth,
        max_rounds=req.max_rounds,
    )

    jobs_db[objective.id] = {
        "status": "running",
        "objective": objective.model_dump(),
        "logs": [],
        "report": None,
    }

    async def _runner():
        def _log(msg: str):
            jobs_db[objective.id]["logs"].append(msg)

        orch = ResearchOrchestrator(on_progress=_log)
        try:
            report = await orch.run(objective)
            jobs_db[objective.id]["status"] = "completed"
            jobs_db[objective.id]["report"] = report.model_dump()
        except Exception as e:
            jobs_db[objective.id]["status"] = "failed"
            jobs_db[objective.id]["error"] = str(e)

    asyncio.create_task(_runner())
    return {"job_id": objective.id, "status": "running"}


@app.get("/api/research/{job_id}")
async def get_research_status(job_id: str):
    """Get status and logs for a research job."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]


@app.get("/api/research/{job_id}/markdown")
async def get_research_markdown(job_id: str):
    """Get the full research report formatted as Markdown."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs_db[job_id]
    if job["status"] != "completed" or not job["report"]:
        raise HTTPException(status_code=400, detail="Job is not yet completed")

    report = FinalReport.model_validate(job["report"])
    return {"markdown": report.to_markdown()}
