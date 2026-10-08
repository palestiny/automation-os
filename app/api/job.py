from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_authorization_context
from app.application.authorization import AuthorizationContext
from app.core.dependencies import job_manager
from app.schemas.job.response import JobStatusResponse

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(
    job_id: UUID,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    if context.is_system or context.tenant_id is None:
        raise HTTPException(status_code=403, detail="A tenant identity is required")
    job = job_manager.get_job(str(job_id), context.tenant_id.value)
    if job is None:
        # Same response for absent and cross-tenant jobs prevents ID enumeration.
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**job)
