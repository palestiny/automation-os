from __future__ import annotations

import pytest

from app.application.workflow_persistence import PersistWorkflow
from app.domain.workflow import Workflow, WorkflowState


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self.saved: list[Workflow] = []

    def save(self, workflow: Workflow) -> None:
        self.saved.append(workflow)


def make_draft() -> Workflow:
    return Workflow.create(name="Generated workflow")


def test_persists_draft_workflow_without_publishing_or_executing():
    repository = InMemoryWorkflowRepository()
    use_case = PersistWorkflow(repository)
    workflow = make_draft()

    result = use_case.execute(workflow)

    assert result is workflow
    assert repository.saved == [workflow]
    assert workflow.state is WorkflowState.DRAFT
    assert not hasattr(result, "execution")


def test_rejects_non_workflow():
    repository = InMemoryWorkflowRepository()
    use_case = PersistWorkflow(repository)

    with pytest.raises(TypeError, match="Workflow"):
        use_case.execute(object())
