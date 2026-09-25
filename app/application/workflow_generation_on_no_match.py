from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.application.workflow_candidate_materialization import MaterializeWorkflowCandidate
from app.application.workflow_generation import WorkflowCandidate
from app.application.workflow_generation_validation import ValidateWorkflowCandidate
from app.application.workflow_generator import WorkflowGenerator
from app.application.workflow_selection import (
    SelectWorkflow,
    WorkflowSelectionStatus,
)
from app.domain.intent import Intent
from app.domain.workflow import Workflow


class WorkflowGenerationOnNoMatchStatus(Enum):
    SELECTED = "selected"
    GENERATED = "generated"
    CLARIFICATION_REQUIRED = "clarification_required"
    INVALID_PARAMETERS = "invalid_parameters"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class WorkflowGenerationOnNoMatchResult:
    status: WorkflowGenerationOnNoMatchStatus
    workflow_id: UUID | None = None
    workflow: Workflow | None = None
    candidate: WorkflowCandidate | None = None
    missing_parameters: tuple[str, ...] = ()


class GenerateWorkflowOnNoMatch:
    """Generate only after deterministic workflow selection returns NO_MATCH."""

    def __init__(
        self,
        selector: SelectWorkflow,
        generator: WorkflowGenerator,
        validator: ValidateWorkflowCandidate,
        materializer: MaterializeWorkflowCandidate,
    ) -> None:
        self._selector = selector
        self._generator = generator
        self._validator = validator
        self._materializer = materializer

    @staticmethod
    def _status(selection_status: WorkflowSelectionStatus) -> WorkflowGenerationOnNoMatchStatus:
        return WorkflowGenerationOnNoMatchStatus(selection_status.value)

    def execute(self, intent: Intent) -> WorkflowGenerationOnNoMatchResult:
        selection = self._selector.execute(intent)

        if selection.status is not WorkflowSelectionStatus.NO_MATCH:
            return WorkflowGenerationOnNoMatchResult(
                status=self._status(selection.status),
                workflow_id=selection.workflow_id,
                missing_parameters=selection.missing_parameters,
            )

        candidate = self._generator.generate(intent)
        validated_candidate = self._validator.execute(candidate)
        workflow = self._materializer.execute(validated_candidate)

        return WorkflowGenerationOnNoMatchResult(
            status=WorkflowGenerationOnNoMatchStatus.GENERATED,
            workflow_id=workflow.id,
            workflow=workflow,
        )
