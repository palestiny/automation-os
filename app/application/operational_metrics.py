from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TimingMetric:
    """Provider-neutral timing evidence for an operational event."""

    name: str
    duration_ms: float
    outcome: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Metric name cannot be empty")
        if self.duration_ms < 0:
            raise ValueError("Metric duration cannot be negative")


class OperationalMetrics(Protocol):
    """Application port for bounded operational timing metrics."""

    def record_timing(
        self,
        name: str,
        duration_ms: float,
        *,
        outcome: str | None = None,
    ) -> None:
        ...


class NoopOperationalMetrics:
    """Default metrics sink when no operational backend is configured."""

    def record_timing(
        self,
        name: str,
        duration_ms: float,
        *,
        outcome: str | None = None,
    ) -> None:
        return None
