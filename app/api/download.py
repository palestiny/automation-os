from fastapi import APIRouter, BackgroundTasks

from app.core.dependencies import job_manager
from app.schemas.download.request import DownloadRequest
from app.schemas.job.response import JobResponse
from app.services.youtube_service import YouTubeService

router = APIRouter()

youtube = YouTubeService()


def progress_callback(progress):

    job_manager.update_progress(

        job_id=job_id,

        progress=progress.progress,

        status=progress.status,

        message="Downloading video..."
    )


@router.post(
    "/download",
    response_model=JobResponse
)
def download_video(
    request: DownloadRequest,
    background_tasks: BackgroundTasks
):

    job_id = job_manager.create_job()

    background_tasks.add_task(
        download_task,
        job_id,
        str(request.url)
    )

    return JobResponse(
        job_id=job_id
    )