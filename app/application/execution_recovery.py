from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from app.domain.execution import Execution, ExecutionState
from app.domain.repositories import ExecutionRepository


@dataclass(frozen=True)
class ExecutionRecoveryPolicy:
    """Operational policy for identifying stale RUNNING executions."""

    stale_after: timedelta

    def __post_init__(self) -> None:
        if self.stale_after <= timedelta(0):
            raise ValueError("Recovery stale_after must be greater than zero")

    def is_stale(self, execution: Execution, now: datetime) -> bool:
        if execution.state is not ExecutionState.RUNNING:
            return False
        if execution.started_at is None:
            return False
        return now - execution.started_at >= self.stale_after


class RecoverStaleExecution:
    """Recover one stale RUNNING execution without executing workflow work."""

    def __init__(
        self,
        execution_repository: ExecutionRepository,
        policy: ExecutionRecoveryPolicy,
    ) -> None:
        self._execution_repository = execution_repository
        self._policy = policy

    def execute(
        self,
        execution_id: UUID,
        *,
        now: datetime,
    ) -> Execution | None:
        execution = self._execution_repository.get(execution_id)
        if execution is None:
            raise ValueError(f"Execution not found: {execution_id}")

        if not self._policy.is_stale(execution, now):
            return None

        recovered = deepcopy(execution)
        recovered.recover_stale()

        if not self._execution_repository.save_if_state(
            recovered,
            ExecutionState.RUNNING,
        ):
            return None

        return recovered


class RecoverStaleExecutions:
    """Recover a deterministic batch of stale RUNNING executions sequentially."""

    def __init__(
        self,
        execution_repository: ExecutionRepository,
        recovery: RecoverStaleExecution,
    ) -> None:
        self._execution_repository = execution_repository
        self._recovery = recovery

    def execute(self, *, now: datetime) -> tuple[Execution, ...]:
        recovered: list[Execution] = []
        for execution in sorted(
            self._execution_repository.all(),
            key=lambda item: str(item.id),
        ):
            result = self._recovery.execute(execution.id, now=now)
            if result is not None:
                recovered.append(result)
        return tuple(recovered)
