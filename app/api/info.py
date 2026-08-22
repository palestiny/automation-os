from fastapi import APIRouter

from app.schemas.download.request import DownloadRequest
from app.schemas.download.response import VideoInfoResponse
from app.services.youtube_service import YouTubeService

router = APIRouter()

youtube = YouTubeService()


@router.post(
    "/info",
    response_model=VideoInfoResponse
)
def get_video_info(request: DownloadRequest):

    return youtube.get_video_info(str(request.url))