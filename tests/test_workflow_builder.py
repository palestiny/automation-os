import pytest

from app.domain.workflow import Workflow, WorkflowState
from app.domain.workflow_builder import WorkflowBuilder


def test_builder_creates_draft_workflow():
    workflow = (
        WorkflowBuilder("AutoReel Pipeline")
        .build()
    )

    assert workflow.name == "AutoReel Pipeline"
    assert workflow.state == WorkflowState.DRAFT
    assert workflow.steps == ()


def test_builder_adds_steps_in_collection_order():
    workflow = (
        WorkflowBuilder("AutoReel Pipeline")
        .add_step("Download video", "video_download")
        .add_step("Transcribe", "transcription")
        .build()
    )

    assert [step.name for step in workflow.steps] == [
        "Download video",
        "Transcribe",
    ]
    assert [step.capability for step in workflow.steps] == [
        "video_download",
        "transcription",
    ]


def test_builder_returns_a_workflow():
    workflow = WorkflowBuilder("AutoReel Pipeline").build()

    assert isinstance(workflow, Workflow)


def test_builder_does_not_bypass_workflow_name_invariant():
    with pytest.raises(ValueError, match="Workflow name cannot be empty"):
        WorkflowBuilder("   ").build()


def test_builder_does_not_bypass_workflow_step_invariants():
    builder = WorkflowBuilder("AutoReel Pipeline")

    with pytest.raises(ValueError, match="WorkflowStep capability cannot be empty"):
        builder.add_step("Download video", "   ")
