import pytest

from app.application.workflow_builder import WorkflowBuilder
from app.domain.workflow import WorkflowState, WorkflowStep


def test_application_builder_creates_ordered_draft_workflow():
    first = WorkflowStep.create(name="Acquire", capability="content.acquire")
    second = WorkflowStep.create(name="Transcribe", capability="content.transcribe")

    workflow = WorkflowBuilder().create(
        "Content pipeline",
        [first, second],
        supported_goals=["create_content"],
    )

    assert workflow.state == WorkflowState.DRAFT
    assert workflow.steps == (first, second)
    assert workflow.supported_goals == ("create_content",)


def test_application_builder_rejects_empty_workflow():
    with pytest.raises(ValueError, match="at least one step"):
        WorkflowBuilder().create("Empty", [])


def test_application_builder_rejects_non_workflow_step():
    with pytest.raises(ValueError, match="WorkflowStep instances"):
        WorkflowBuilder().create("Invalid", [object()])  # type: ignore[list-item]


def test_application_builder_rejects_duplicate_step_identities():
    step = WorkflowStep.create(name="Acquire", capability="content.acquire")
    duplicate = WorkflowStep(id=step.id, name="Transcribe", capability="content.transcribe")

    with pytest.raises(ValueError, match="identities must be unique"):
        WorkflowBuilder().create("Invalid", [step, duplicate])


def test_application_builder_preserves_metadata_without_execution():
    workflow = WorkflowBuilder().create(
        "Content pipeline",
        [WorkflowStep.create(name="Acquire", capability="content.acquire")],
        automation_domain="content",
        discovery_tags=["video", "content"],
    )

    assert workflow.automation_domain == "content"
    assert workflow.discovery_tags == ("video", "content")
    assert workflow.state == WorkflowState.DRAFT
