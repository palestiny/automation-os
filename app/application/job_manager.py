from uuid import UUID

from app.domain.execution import Execution


class JobManager:
    """Application-level registry for active executions.

    JobManager owns registration and lookup only. Execution remains
    responsible for lifecycle state transitions.
    """

    def __init__(self) -> None:
        self._executions: dict[UUID, Execution] = {}

    def register(self, execution: Execution) -> UUID:
        if execution.id in self._executions:
            raise ValueError(
                f"Execution {execution.id} is already registered"
            )

        self._executions[execution.id] = execution
        return execution.id

    def get(self, execution_id: UUID) -> Execution:
        return self._executions[execution_id]
