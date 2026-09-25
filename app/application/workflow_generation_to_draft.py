from __future__ import annotations

from app.application.workflow_candidate_materialization import MaterializeWorkflowCandidate
from app.application.workflow_generation import WorkflowCandidate
from app.application.workflow_persistence import PersistWorkflow
from app.domain.workflow import Workflow


class CreateDraftWorkflowFromCandidate:
    """Compatibility facade for materializing and persisting a generated draft."""

    def __init__(self, repository) -> None:
        self._materializer = MaterializeWorkflowCandidate()
        self._persistence = PersistWorkflow(repository)

    def execute(self, candidate: WorkflowCandidate) -> Workflow:
        if not isinstance(candidate, WorkflowCandidate):
            raise TypeError("candidate must be a WorkflowCandidate instance")
        if not candidate.steps:
            raise ValueError("Workflow candidate must contain at least one step")
        return self._persistence.execute(self._materializer.execute(candidate))
