from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ReportSpecification:
    title: str
    metrics: tuple[str, ...]
    filters: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Report title cannot be empty")
        if any(not isinstance(metric, str) or not metric.strip() for metric in self.metrics):
            raise ValueError("Report metrics must be non-empty strings")
        if len(set(self.metrics)) != len(self.metrics):
            raise ValueError("Report metrics must be unique")


@dataclass(frozen=True)
class ReportAsset:
    title: str
    rows: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Report title cannot be empty")
