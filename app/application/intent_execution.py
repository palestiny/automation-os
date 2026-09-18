from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.workflow_selection import SelectWorkflow, WorkflowSelectionStatus
from app.domain.execution import Execution
from app.domain.intent import Intent
from app.domain.workflow import Workflow


class IntentExecutionStatus(Enum):
    STARTED = "started"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class IntentExecutionResult:
    status: IntentExecutionStatus
    execution: Execution | None = None


class ExecuteIntent:
    """Select a published workflow for an Intent and start it through the existing use case."""

    def __init__(
        self,
        workflows: list[Workflow],
        start_workflow_execution: StartWorkflowExecution,
    ) -> None:
        if not isinstance(start_workflow_execution, StartWorkflowExecution):
            raise TypeError(
                "start_workflow_execution must be a StartWorkflowExecution instance"
            )

        self._selector = SelectWorkflow(workflows)
        self._start_workflow_execution = start_workflow_execution

    def execute(self, intent: Intent) -> IntentExecutionResult:
        selection = self._selector.execute(intent)

        if selection.status == WorkflowSelectionStatus.NO_MATCH:
            return IntentExecutionResult(IntentExecutionStatus.NO_MATCH)

        if selection.status == WorkflowSelectionStatus.AMBIGUOUS:
            return IntentExecutionResult(IntentExecutionStatus.AMBIGUOUS)

        execution = self._start_workflow_execution.execute(selection.workflow_id)
        return IntentExecutionResult(IntentExecutionStatus.STARTED, execution)
