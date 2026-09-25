from __future__ import annotations

import pytest

from app.application.workflow_publication import PublishWorkflow
from app.domain.workflow import Workflow, WorkflowState, WorkflowStep


def _draft_workflow() -> Workflow:
    return Workflow.create(
        name="publishable workflow",
        steps=[WorkflowStep.create(name="step", capability="known.capability")],
    )


def test_publish_workflow_explicitly_publishes_draft() -> None:
    workflow = _draft_workflow()

    result = PublishWorkflow().execute(workflow)

    assert result is workflow
    assert workflow.state is WorkflowState.PUBLISHED


def test_publish_workflow_rejects_already_published_workflow() -> None:
    workflow = _draft_workflow()
    workflow.publish()

    with pytest.raises(ValueError, match="DRAFT"):
        PublishWorkflow().execute(workflow)


def test_publish_workflow_does_not_execute_workflow() -> None:
    workflow = _draft_workflow()

    result = PublishWorkflow().execute(workflow)

    assert result.state is WorkflowState.PUBLISHED
    assert not hasattr(result, "execution")
