from __future__ import annotations

from uuid import UUID

from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.trigger_matcher import TriggerMatcher
from app.domain.event import Event
from app.domain.execution import Execution
from app.domain.repositories import WorkflowRepository
from app.domain.workflow import WorkflowState


class TriggerInvocation:
    """Match a normalized event to published workflows and request execution."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        start_workflow_execution: StartWorkflowExecution,
        trigger_matcher: TriggerMatcher | None = None,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._start_workflow_execution = start_workflow_execution
        self._trigger_matcher = trigger_matcher or TriggerMatcher()

    def invoke(self, event: Event) -> tuple[Execution, ...]:
        matching_workflows = sorted(
            (
                workflow
                for workflow in self._workflow_repository.all()
                if workflow.state is WorkflowState.PUBLISHED
                and self._trigger_matcher.match(event, workflow) is not None
            ),
            key=lambda workflow: workflow.id,
        )

        return tuple(
            self._start_workflow_execution.execute(
                workflow.id,
                idempotency_key=self._external_event_key(event, workflow.id),
            )
            for workflow in matching_workflows
        )

    @staticmethod
    def _external_event_key(event: Event, workflow_id: UUID) -> str | None:
        if event.external_event_id is None:
            return None
        return f"external-event:{event.source}:{event.external_event_id}:{workflow_id}"
