from fastapi import APIRouter, HTTPException

from app.core.dependencies import job_manager
from app.schemas.job.response import JobStatusResponse

router = APIRouter()


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse
)
def get_job(job_id: str):

    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return JobStatusResponse(**job)