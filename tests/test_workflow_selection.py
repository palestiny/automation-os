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


def test_select_workflow_requires_declared_parameters():
    workflow = Workflow.create(
        name="Reporting workflow",
        steps=[WorkflowStep.create(name="Run", capability="report")],
        supported_goals=["generate_report"],
        required_parameters=["source"],
    )
    workflow.publish()

    selector = SelectWorkflow([workflow])

    assert selector.execute(Intent.create("generate_report", {"source": "sales"})).status == WorkflowSelectionStatus.SELECTED
    assert selector.execute(Intent.create("generate_report", {})).status == WorkflowSelectionStatus.MISSING_PARAMETERS


def test_select_workflow_keeps_goal_only_workflows_backward_compatible():
    workflow = Workflow.create(
        name="Simple workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=["simple_task"],
    )
    workflow.publish()

    result = SelectWorkflow([workflow]).execute(Intent.create("simple_task", {"extra": 1}))

    assert result.status == WorkflowSelectionStatus.SELECTED


def test_workflow_required_parameters_are_immutable_and_unique():
    workflow = Workflow.create(
        name="Reporting workflow",
        steps=[WorkflowStep.create(name="Run", capability="report")],
        required_parameters=["source", "format"],
    )

    assert workflow.required_parameters == ("source", "format")

    with pytest.raises(ValueError, match="unique"):
        Workflow.create(
            name="Invalid",
            steps=[WorkflowStep.create(name="Run", capability="run")],
            required_parameters=["source", "source"],
        )
