from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from app.application.download_progress import DownloadProgress


MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
SOCKET_TIMEOUT_SECONDS = 10


class YouTubeService:
    """Constrained YouTube extractor/downloader infrastructure adapter."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = (storage_path or Path("storage/videos")).resolve()
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _build_options(
        self,
        *,
        download: bool = False,
        progress_hook: Callable[[DownloadProgress], None] | None = None,
    ) -> dict[str, object]:
        options: dict[str, object] = {
            "quiet": True,
            "noplaylist": True,
            "socket_timeout": SOCKET_TIMEOUT_SECONDS,
            "retries": 1,
            "fragment_retries": 1,
            "max_downloads": 1,
        }
        if download:
            options.update(
                {
                    "format": "best[ext=mp4]/best",
                    "max_filesize": MAX_DOWNLOAD_BYTES,
                    "restrictfilenames": True,
                    "outtmpl": str(self.storage_path / "%(id)s.%(ext)s"),
                    "progress_hooks": [
                        lambda data: self._notify_progress(data, progress_hook)
                    ],
                }
            )
        return options

    def _extract(
        self,
        url: str,
        *,
        download: bool = False,
        progress_hook: Callable[[DownloadProgress], None] | None = None,
    ):
        with YoutubeDL(
            self._build_options(download=download, progress_hook=progress_hook)
        ) as ydl:
            return ydl.extract_info(url, download=download)

    def get_video_info(self, url: str) -> dict[str, object]:
        info = self._extract(url)
        return {
            "title": info.get("title") or "Untitled",
            "duration": int(info.get("duration") or 0),
            "uploader": info.get("uploader") or "Unknown",
        }

    def download_video(
        self,
        url: str,
        progress_hook: Callable[[DownloadProgress], None] | None = None,
    ) -> dict[str, object]:
        info = self._extract(url, download=True, progress_hook=progress_hook)
        requested = info.get("requested_downloads") or []
        filepath = (
            requested[0].get("filepath")
            if requested and isinstance(requested[0], dict)
            else None
        )
        filepath = filepath or str(self.storage_path / f"{info['id']}.{info.get('ext', 'mp4')}")
        path = Path(filepath).resolve()
        if self.storage_path not in path.parents:
            raise DownloadError("Resolved download path escaped the storage directory")
        if path.exists() and path.stat().st_size > MAX_DOWNLOAD_BYTES:
            path.unlink(missing_ok=True)
            raise DownloadError("Download exceeded the configured size limit")
        return {
            "success": True,
            "message": "Video downloaded successfully.",
            "title": str(info.get("title") or info["id"]),
            "file": str(path.relative_to(Path.cwd())),
        }

    @staticmethod
    def _notify_progress(data: dict[str, object], callback) -> None:
        if callback is None:
            return
        status = data.get("status")
        downloaded = int(data.get("downloaded_bytes") or 0)
        total = int(
            data.get("total_bytes")
            or data.get("total_bytes_estimate")
            or 0
        )
        if downloaded > MAX_DOWNLOAD_BYTES or total > MAX_DOWNLOAD_BYTES:
            raise DownloadError("Download exceeded the configured size limit")
        if status == "downloading":
            progress = min(99, int(downloaded * 100 / total)) if total else 0
            callback(
                DownloadProgress(
                    progress=progress,
                    status="downloading",
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                )
            )
        elif status == "finished":
            callback(
                DownloadProgress(
                    progress=99,
                    status="processing",
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                )
            )
