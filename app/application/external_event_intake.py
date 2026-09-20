from __future__ import annotations

from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.trigger_invocation import TriggerInvocation
from app.domain.execution import Execution
from app.domain.external_event import ExternalEvent
from app.domain.repositories import WorkflowRepository


class ExternalEventIntake:
    """Normalize an external event and delegate to the existing trigger boundary."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        start_workflow_execution: StartWorkflowExecution,
    ) -> None:
        self._trigger_invocation = TriggerInvocation(
            workflow_repository,
            start_workflow_execution,
        )

    def accept(self, external_event: ExternalEvent) -> tuple[Execution, ...]:
        return self._trigger_invocation.invoke(
            external_event.to_event(),
            idempotency_key=external_event.deduplication_key,
        )
