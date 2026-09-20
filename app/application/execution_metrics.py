from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.execution import ExecutionState
from app.domain.repositories import ExecutionHistoryRepository, ExecutionRepository


@dataclass(frozen=True)
class ExecutionMetrics:
    window_start: datetime
    window_end: datetime
    total_executions: int
    state_counts: dict[str, int]
    completed_duration_seconds: dict[str, float | int] | None
    retry_count: int
    recovery_count: int
    workflow_breakdown: dict[str, int]
    workflow_version_breakdown: dict[str, int]
    attempt_distribution: dict[int, int]


class GetExecutionMetrics:
    """Calculates read-only operational metrics from persisted execution evidence."""

    def __init__(
        self,
        execution_repository: ExecutionRepository,
        history_repository: ExecutionHistoryRepository,
    ) -> None:
        self._execution_repository = execution_repository
        self._history_repository = history_repository

    def execute(
        self,
        window_start: datetime,
        window_end: datetime,
    ) -> ExecutionMetrics:
        if window_start >= window_end:
            raise ValueError("window_start must be before window_end")

        executions = tuple(
            execution
            for execution in self._execution_repository.all()
            if execution.started_at is not None
            and window_start <= execution.started_at < window_end
        )

        state_counts = {state.value: 0 for state in ExecutionState}
        workflow_breakdown: dict[str, int] = {}
        workflow_version_breakdown: dict[str, int] = {}
        attempt_distribution: dict[int, int] = {}
        durations: list[float] = []
        retry_count = 0
        recovery_count = 0

        for execution in sorted(executions, key=lambda item: str(item.id)):
            state_counts[execution.state.value] += 1

            workflow_key = str(execution.workflow_id)
            workflow_breakdown[workflow_key] = (
                workflow_breakdown.get(workflow_key, 0) + 1
            )

            version_key = (
                str(execution.workflow_version_id)
                if execution.workflow_version_id is not None
                else "unversioned"
            )
            workflow_version_breakdown[version_key] = (
                workflow_version_breakdown.get(version_key, 0) + 1
            )

            attempt_distribution[execution.attempt] = (
                attempt_distribution.get(execution.attempt, 0) + 1
            )

            if (
                execution.state is ExecutionState.COMPLETED
                and execution.started_at is not None
                and execution.finished_at is not None
            ):
                durations.append(
                    (execution.finished_at - execution.started_at).total_seconds()
                )

            for event in self._history_repository.list(execution.id):
                if event.event_type == "execution.retrying":
                    retry_count += 1
                elif event.event_type == "execution.recovered_stale":
                    recovery_count += 1

        completed_duration_seconds = None
        if durations:
            completed_duration_seconds = {
                "count": len(durations),
                "total": float(sum(durations)),
                "average": float(sum(durations) / len(durations)),
                "minimum": float(min(durations)),
                "maximum": float(max(durations)),
            }

        return ExecutionMetrics(
            window_start=window_start,
            window_end=window_end,
            total_executions=len(executions),
            state_counts=state_counts,
            completed_duration_seconds=completed_duration_seconds,
            retry_count=retry_count,
            recovery_count=recovery_count,
            workflow_breakdown=workflow_breakdown,
            workflow_version_breakdown=workflow_version_breakdown,
            attempt_distribution=dict(sorted(attempt_distribution.items())),
        )
