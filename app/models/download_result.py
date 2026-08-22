from dataclasses import dataclass


@dataclass
class DownloadResult:
    title: str
    file: str