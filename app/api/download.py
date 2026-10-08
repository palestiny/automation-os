from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.auth import get_authorization_context
from app.application.authorization import AuthorizationContext
from app.application.download_jobs import DownloadJobCapacityExceeded
from app.core.dependencies import job_manager
from app.infrastructure.media.youtube_service import YouTubeService
from app.schemas.download.request import DownloadRequest
from app.schemas.job.response import JobResponse

router = APIRouter(tags=["download"])
youtube = YouTubeService()
logger = logging.getLogger("automation_os.download")


def _download_task(job_id: str, url: str, tenant_id: UUID) -> None:
    def progress_callback(progress) -> None:
        job_manager.update_progress(
            job_id=job_id,
            tenant_id=tenant_id,
            progress=progress.progress,
            status=progress.status,
            message="Downloading video...",
        )

    try:
        result = youtube.download_video(url, progress_hook=progress_callback)
        job_manager.set_title(job_id, tenant_id, str(result["title"]))
        job_manager.complete(
            job_id,
            tenant_id,
            str(result.get("message", "Download completed")),
        )
    except Exception:
        # Do not return/log raw provider exceptions, which can contain source URLs.
        logger.warning("download.failed job_id=%s", job_id)
        job_manager.set_error(
            job_id,
            tenant_id,
            "Download failed. Verify the video is available and within the size limit.",
        )


@router.post("/download", response_model=JobResponse)
def download_video(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    if context.is_system or context.tenant_id is None:
        raise HTTPException(status_code=403, detail="A tenant identity is required")
    try:
        job_id = job_manager.create_job(context.tenant_id.value)
    except DownloadJobCapacityExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    background_tasks.add_task(
        _download_task,
        job_id,
        str(request.url),
        context.tenant_id.value,
    )
    return JobResponse(job_id=job_id)
