from uuid import uuid4

import pytest

from app.application.workflow_selection import (
    SelectWorkflow,
    WorkflowSelectionStatus,
)
from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowState, WorkflowStep


def make_workflow(*goals: str) -> Workflow:
    return Workflow.create(
        name="Content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=list(goals),
    )


def test_workflow_declares_supported_goals():
    workflow = make_workflow("create_short_video", "publish_content")

    assert workflow.supported_goals == (
        "create_short_video",
        "publish_content",
    )


def test_selector_selects_published_workflow_matching_intent():
    workflow = make_workflow("create_short_video")
    workflow.publish()

    result = SelectWorkflow([workflow]).execute(
        Intent.create("create_short_video")
    )

    assert result.status == WorkflowSelectionStatus.SELECTED
    assert result.workflow_id == workflow.id


def test_selector_ignores_draft_matching_workflow():
    workflow = make_workflow("create_short_video")

    result = SelectWorkflow([workflow]).execute(
        Intent.create("create_short_video")
    )

    assert result.status == WorkflowSelectionStatus.NO_MATCH
    assert result.workflow_id is None


def test_selector_returns_no_match_when_goal_is_unknown():
    workflow = make_workflow("publish_content")
    workflow.publish()

    result = SelectWorkflow([workflow]).execute(
        Intent.create("create_short_video")
    )

    assert result.status == WorkflowSelectionStatus.NO_MATCH
    assert result.workflow_id is None


def test_selector_returns_ambiguous_when_multiple_workflows_match():
    first = make_workflow("create_short_video")
    second = make_workflow("create_short_video")
    first.publish()
    second.publish()

    result = SelectWorkflow([first, second]).execute(
        Intent.create("create_short_video")
    )

    assert result.status == WorkflowSelectionStatus.AMBIGUOUS
    assert result.workflow_id is None


def test_workflow_selection_result_is_explicit_for_invalid_workflow_input():
    with pytest.raises(ValueError, match="Workflow must be a Workflow instance"):
        SelectWorkflow([object()]).execute(Intent.create("create_short_video"))
