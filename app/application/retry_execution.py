from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from app.domain.execution import Execution
from app.domain.repositories import ExecutionRepository
from app.domain.retry_policy import RetryPolicy


@dataclass(frozen=True)
class ManualRetryContext:
    """Auditable context for an explicitly authorized manual retry."""

    actor_id: str
    reason: str

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("Manual retry actor_id cannot be empty")
        if not self.reason.strip():
            raise ValueError("Manual retry reason cannot be empty")


class RetryExecution:
    """Retry a failed execution while separating policy-driven and manual authority."""

    def __init__(
        self,
        execution_repository: ExecutionRepository,
        retry_policy: RetryPolicy | None = None,
        manual_authorizer: Callable[[Execution, ManualRetryContext], None] | None = None,
    ) -> None:
        self._execution_repository = execution_repository
        self._retry_policy = retry_policy
        self._manual_authorizer = manual_authorizer

    def execute(
        self,
        execution_id: UUID,
        *,
        manual_context: ManualRetryContext | None = None,
    ) -> Execution:
        execution = self._execution_repository.get(execution_id)
        if execution is None:
            raise ValueError(f"Execution not found: {execution_id}")

        policy_allows_retry = (
            self._retry_policy is None or self._retry_policy.can_retry(execution)
        )
        if not policy_allows_retry:
            if manual_context is None:
                raise ValueError("RetryPolicy does not allow another automatic retry")
            if self._manual_authorizer is None:
                raise PermissionError("Manual retry authorization is required")
            self._manual_authorizer(execution, manual_context)

        execution.retry()
        self._execution_repository.save(execution)

        return execution
