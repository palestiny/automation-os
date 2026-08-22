from pydantic import BaseModel


class VideoInfoResponse(BaseModel):
    title: str
    duration: int
    uploader: str


class DownloadResponse(BaseModel):
    success: bool
    title: str
    file: str
    message: str