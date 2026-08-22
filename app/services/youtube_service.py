from pathlib import Path
from yt_dlp import YoutubeDL
from app.models.download_progress import DownloadProgress
import os

class YouTubeService:

    def __init__(self):

        self.storage_path = Path("storage/videos")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _build_options(self, download: bool = False, progress_hook=None):

        options = {
            "quiet": True
        }

        if download:

            options.update({
                "format": "mp4",
                "outtmpl": str(self.storage_path / "%(title)s.%(ext)s")
            })

            if progress_hook:
                options["progress_hooks"] = [

                lambda data:

                self._notify_progress(
                    data,
                    progress_hook
                )
            ]

        return options

    def _extract(self, url: str, download: bool = False,progress_hook=None):

        options = self._build_options(download,progress_hook)

        with YoutubeDL(options) as ydl:

            return ydl.extract_info(url, download=download)

    def get_video_info(self, url: str):

        info = self._extract(url)

        return {
            "title": info["title"],
            "duration": info["duration"],
            "uploader": info["uploader"]
        }

    def download_video(self, url: str,progress_hook=None):
        os.makedirs("storage/videos", exist_ok=True)

        options = {
            "outtmpl": "storage/videos/%(title)s.%(ext)s",
            "format": "mp4",                
            "quiet": True,
            }

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True,progress_hook=progress_hook)

        return {
           "success": True,
           "message": "Video downloaded successfully.",
           "title": info["title"],
           "file": f"storage/videos/{info['title']}.mp4"
        }
    def _notify_progress(
        self,
        data,
        progress_callback
    ):

        if progress_callback is None:
            return

        status = data.get("status")

        if status == "downloading":

            downloaded = data.get("downloaded_bytes", 0)

            total = (
                data.get("total_bytes")
                or data.get("total_bytes_estimate")
                or 0
            )

            if total > 0:

                progress = int(downloaded * 100 / total)

                progress_callback(

                    DownloadProgress(

                        progress=progress,

                        status="downloading"
                    )
                )

        elif status == "finished":

            progress_callback(

                DownloadProgress(

                    progress=100,

                    status="finished"
                )
            )