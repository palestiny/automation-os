import pytest

from app.domain.workflow import WorkflowState
from app.application.workflow_builder import WorkflowBuilder


def test_builder_creates_draft_workflow():
    workflow = (
        WorkflowBuilder()
        .name("Content Pipeline")
        .add_step("Download video", "video_download")
        .build()
    )

    assert workflow.name == "Content Pipeline"
    assert workflow.state == WorkflowState.DRAFT
    assert len(workflow.steps) == 1
    assert workflow.steps[0].name == "Download video"
    assert workflow.steps[0].capability == "video_download"


def test_builder_preserves_step_order():
    workflow = (
        WorkflowBuilder()
        .name("Content Pipeline")
        .add_step("Download video", "video_download")
        .add_step("Transcribe", "transcription")
        .build()
    )

    assert [step.name for step in workflow.steps] == [
        "Download video",
        "Transcribe",
    ]


def test_builder_requires_name():
    with pytest.raises(ValueError):
        WorkflowBuilder().add_step("Download video", "video_download").build()


def test_builder_requires_at_least_one_step():
    with pytest.raises(ValueError):
        WorkflowBuilder().name("Content Pipeline").build()
