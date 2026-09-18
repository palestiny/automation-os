from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.application.workflow_discovery import DiscoverWorkflows, WorkflowDiscoveryQuery
from app.domain.intent import Intent
from app.domain.workflow import Workflow


class WorkflowSelectionStatus(Enum):
    SELECTED = "selected"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class WorkflowSelectionResult:
    status: WorkflowSelectionStatus
    workflow_id: UUID | None = None


class SelectWorkflow:
    """Select exactly one published workflow that satisfies an Intent."""

    def __init__(self, workflows: list[Workflow]) -> None:
        self._discovery = DiscoverWorkflows(workflows)

    def execute(self, intent: Intent) -> WorkflowSelectionResult:
        candidates = self._discovery.execute(
            WorkflowDiscoveryQuery(goal=intent.goal)
        )
        matches = tuple(
            workflow
            for workflow in candidates
            if all(
                parameter in intent.parameters
                for parameter in workflow.required_parameters
            )
        )

        if not matches:
            return WorkflowSelectionResult(WorkflowSelectionStatus.NO_MATCH)

        if len(matches) > 1:
            return WorkflowSelectionResult(WorkflowSelectionStatus.AMBIGUOUS)

        return WorkflowSelectionResult(
            WorkflowSelectionStatus.SELECTED,
            matches[0].id,
        )
