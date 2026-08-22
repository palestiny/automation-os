from dataclasses import dataclass


@dataclass
class DownloadProgress:
    progress: int
    status: str
    downloaded_bytes: int = 0
    total_bytes: int = 0