from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowState


class WorkflowSelectionStatus(Enum):
    SELECTED = "selected"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class WorkflowSelectionResult:
    status: WorkflowSelectionStatus
    workflow_id: UUID | None = None


class SelectWorkflow:
    def __init__(self, workflows: list[Workflow]) -> None:
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflow must be a Workflow instance")
        self._workflows = tuple(workflows)

    def execute(self, intent: Intent) -> WorkflowSelectionResult:
        matches = tuple(
            workflow
            for workflow in self._workflows
            if workflow.state == WorkflowState.PUBLISHED
            and intent.goal in workflow.supported_goals
        )

        if not matches:
            return WorkflowSelectionResult(WorkflowSelectionStatus.NO_MATCH)

        if len(matches) > 1:
            return WorkflowSelectionResult(WorkflowSelectionStatus.AMBIGUOUS)

        return WorkflowSelectionResult(
            WorkflowSelectionStatus.SELECTED,
            matches[0].id,
        )
