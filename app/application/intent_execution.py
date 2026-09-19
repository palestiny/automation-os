from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.workflow_selection import SelectWorkflow, WorkflowSelectionStatus
from app.domain.execution import Execution
from app.domain.intent import Intent
from app.domain.workflow import Workflow


class IntentExecutionStatus(Enum):
    STARTED = "started"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"
    CLARIFICATION_REQUIRED = "clarification_required"
    INVALID_GOAL = "invalid_goal"


@dataclass(frozen=True)
class IntentExecutionResult:
    status: IntentExecutionStatus
    execution: Execution | None = None
    missing_parameters: tuple[str, ...] = ()


class ExecuteIntent:
    """Select a published workflow for an Intent and start it through the existing use case."""

    def __init__(
        self,
        workflows: list[Workflow],
        start_workflow_execution: StartWorkflowExecution,
        goal_catalog: IntentGoalCatalog | None = None,
    ) -> None:
        if not isinstance(start_workflow_execution, StartWorkflowExecution):
            raise TypeError(
                "start_workflow_execution must be a StartWorkflowExecution instance"
            )
        if goal_catalog is not None and not isinstance(goal_catalog, IntentGoalCatalog):
            raise TypeError("goal_catalog must be an IntentGoalCatalog instance")

        self._selector = SelectWorkflow(workflows)
        self._start_workflow_execution = start_workflow_execution
        self._goal_catalog = goal_catalog

    def execute(self, intent: Intent) -> IntentExecutionResult:
        if self._goal_catalog is not None and not self._goal_catalog.contains(intent.goal):
            return IntentExecutionResult(IntentExecutionStatus.INVALID_GOAL)

        selection = self._selector.execute(intent)

        if selection.status == WorkflowSelectionStatus.NO_MATCH:
            return IntentExecutionResult(IntentExecutionStatus.NO_MATCH)

        if selection.status == WorkflowSelectionStatus.CLARIFICATION_REQUIRED:
            return IntentExecutionResult(
                IntentExecutionStatus.CLARIFICATION_REQUIRED,
                missing_parameters=selection.missing_parameters,
            )

        if selection.status == WorkflowSelectionStatus.AMBIGUOUS:
            return IntentExecutionResult(IntentExecutionStatus.CLARIFICATION_REQUIRED)

        execution = self._start_workflow_execution.execute(selection.workflow_id)
        return IntentExecutionResult(IntentExecutionStatus.STARTED, execution)
