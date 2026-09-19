from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from app.domain.execution import Execution, ExecutionState
from app.domain.repositories import ExecutionRepository


class HumanDecision(Enum):
    """Explicit outcomes available at a human control point."""

    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class HumanDecisionRequest:
    """Application-level pending human decision associated with an Execution."""

    id: UUID
    execution_id: UUID
    prompt: str
    context: dict[str, object] = field(default_factory=dict)
    decision: HumanDecision | None = None

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Human decision prompt cannot be empty")


class HumanDecisionPort:
    """Application boundary for explicit human decisions.

    The port deliberately owns neither UI nor authorization nor durable
    persistence. Execution state remains authoritative in the Execution
    aggregate.
    """

    def __init__(self, execution_repository: ExecutionRepository) -> None:
        self._execution_repository = execution_repository
        self._requests: dict[UUID, HumanDecisionRequest] = {}

    def request(
        self,
        execution_id: UUID,
        prompt: str,
        context: dict[str, object],
    ) -> HumanDecisionRequest:
        execution = self._get_execution(execution_id)
        self._require_waiting(execution)

        request = HumanDecisionRequest(
            id=uuid4(),
            execution_id=execution_id,
            prompt=prompt,
            context=dict(context),
        )
        self._requests[request.id] = request
        return request

    def decide(
        self,
        request_id: UUID,
        decision: HumanDecision,
    ) -> HumanDecisionRequest:
        request = self._requests.get(request_id)
        if request is None:
            raise ValueError(f"Human decision request not found: {request_id}")

        if request.decision is not None:
            if request.decision is decision:
                return request
            raise ValueError("Human decision request is already decided")

        execution = self._get_execution(request.execution_id)
        self._require_waiting(execution)

        request.decision = decision
        execution.resume()
        self._execution_repository.save(execution)

        return request

    def get(self, request_id: UUID) -> HumanDecisionRequest | None:
        return self._requests.get(request_id)

    def _get_execution(self, execution_id: UUID) -> Execution:
        execution = self._execution_repository.get(execution_id)
        if execution is None:
            raise ValueError(f"Execution not found: {execution_id}")
        return execution

    @staticmethod
    def _require_waiting(execution: Execution) -> None:
        if execution.state is not ExecutionState.WAITING:
            raise ValueError("Human decision requires an execution in WAITING state")
