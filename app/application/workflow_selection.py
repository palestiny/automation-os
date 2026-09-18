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
    MISSING_PARAMETERS = "missing_parameters"
    INVALID_PARAMETERS = "invalid_parameters"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class WorkflowSelectionResult:
    status: WorkflowSelectionStatus
    workflow_id: UUID | None = None


class SelectWorkflow:
    """Select exactly one published workflow that satisfies an Intent."""

    def __init__(self, workflows: list[Workflow]) -> None:
        self._discovery = DiscoverWorkflows(workflows)

    @staticmethod
    def _matches_type(value: object, parameter_type: str) -> bool:
        if parameter_type == "string":
            return isinstance(value, str)
        if parameter_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if parameter_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if parameter_type == "boolean":
            return isinstance(value, bool)
        return False

    def execute(self, intent: Intent) -> WorkflowSelectionResult:
        candidates = self._discovery.execute(
            WorkflowDiscoveryQuery(goal=intent.goal)
        )

        if not candidates:
            return WorkflowSelectionResult(WorkflowSelectionStatus.NO_MATCH)

        complete = tuple(
            workflow
            for workflow in candidates
            if all(
                parameter in intent.parameters
                for parameter in workflow.required_parameters
            )
        )

        if not complete:
            return WorkflowSelectionResult(
                WorkflowSelectionStatus.MISSING_PARAMETERS
            )

        matches = tuple(
            workflow
            for workflow in complete
            if all(
                self._matches_type(intent.parameters[parameter.name], parameter.type)
                for parameter in workflow.parameter_types
            )
        )

        if not matches:
            return WorkflowSelectionResult(
                WorkflowSelectionStatus.INVALID_PARAMETERS
            )

        if len(matches) > 1:
            return WorkflowSelectionResult(WorkflowSelectionStatus.AMBIGUOUS)

        return WorkflowSelectionResult(
            WorkflowSelectionStatus.SELECTED,
            matches[0].id,
        )
