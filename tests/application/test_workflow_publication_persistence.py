from __future__ import annotations

import pytest

from app.application.workflow_publication import PublishWorkflow
from app.domain.workflow import Workflow, WorkflowState, WorkflowStep


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self.saved: list[Workflow] = []

    def save(self, workflow: Workflow) -> None:
        self.saved.append(workflow)


def _draft_workflow() -> Workflow:
    return Workflow.create(
        name="publishable workflow",
        steps=[WorkflowStep.create(name="step", capability="known.capability")],
    )


def test_publish_workflow_publishes_and_persists() -> None:
    workflow = _draft_workflow()
    repository = InMemoryWorkflowRepository()

    result = PublishWorkflow(repository).execute(workflow)

    assert result is workflow
    assert workflow.state is WorkflowState.PUBLISHED
    assert repository.saved == [workflow]


def test_publish_workflow_rejects_already_published_before_persistence() -> None:
    workflow = _draft_workflow()
    workflow.publish()
    repository = InMemoryWorkflowRepository()

    with pytest.raises(ValueError, match="DRAFT"):
        PublishWorkflow(repository).execute(workflow)

    assert repository.saved == []
