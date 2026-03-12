from fastapi import APIRouter, BackgroundTasks

from research_paper_analyser.schemas.requests import AnalyzeRequest
from research_paper_analyser.services.pipeline import run_analysis_pipeline

router = APIRouter()


@router.post("/analyze")
async def analyze_paper(payload: AnalyzeRequest, background_tasks: BackgroundTasks):
    job = run_analysis_pipeline.prepare_job(payload.arxiv_url)
    background_tasks.add_task(run_analysis_pipeline.execute_job, job)
    return {
        "message": "Analysis started in background.",
        "job_id": job.job_id,
        "output_path": job.output_path,
    }
