from fastapi import APIRouter, Depends

from app.api.auth import get_authorization_context
from app.application.authorization import AuthorizationContext
from app.schemas.download.request import DownloadRequest
from app.schemas.download.response import VideoInfoResponse
from app.infrastructure.media.youtube_service import YouTubeService

router = APIRouter(tags=["download"])
youtube = YouTubeService()


@router.post("/info", response_model=VideoInfoResponse)
def get_video_info(
    request: DownloadRequest,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    if context.is_system or context.tenant_id is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="A tenant identity is required")
    return youtube.get_video_info(str(request.url))
