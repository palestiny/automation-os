from __future__ import annotations

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

    def invoke(
        self,
        event: Event,
        *,
        idempotency_key_prefix: str | None = None,
    ) -> tuple[Execution, ...]:
        matching_workflow_ids = sorted(
            workflow_id
            for workflow in self._workflow_repository.all()
            if workflow.state is WorkflowState.PUBLISHED
            for workflow_id in [self._trigger_matcher.match(event, workflow)]
            if workflow_id is not None
        )

        executions = []
        for workflow_id in matching_workflow_ids:
            if idempotency_key_prefix is None:
                executions.append(
                    self._start_workflow_execution.execute(workflow_id)
                )
            else:
                executions.append(
                    self._start_workflow_execution.execute(
                        workflow_id,
                        idempotency_key=f"{idempotency_key_prefix}:{workflow_id}",
                    )
                )
        return tuple(executions)
