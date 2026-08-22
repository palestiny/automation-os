from app.domain.workflow import Workflow, WorkflowStep, WorkflowState
from dataclasses import FrozenInstanceError
import pytest

def test_workflow_can_be_created():
    workflow = Workflow.create(
        name="AutoReel Pipeline",
        steps=[],
    )

    assert workflow.name == "AutoReel Pipeline"
    assert workflow.steps == []



def test_workflow_is_created_as_draft():
    workflow = Workflow.create(
        name="AutoReel Pipeline",
        steps=[],
    )

    assert workflow.state == WorkflowState.DRAFT

def test_workflow_can_be_published():
    workflow = Workflow.create(
        name="AutoReel Pipeline",
        steps=["download"],
    )

    workflow.publish()

    assert workflow.state == WorkflowState.PUBLISHED

def test_workflow_cannot_be_published_twice():
    workflow = Workflow.create(
        name="AutoReel Pipeline",
        steps=["download"],
    )

    workflow.publish()

    with pytest.raises(ValueError):
        workflow.publish()

def test_workflow_step_can_be_created():
    step = WorkflowStep.create(
        name="Download video",
        capability="video_download",
    )

    assert step.name == "Download video"
    assert step.capability == "video_download"

def test_workflow_can_add_step():
    workflow = Workflow.create(
        name="AutoReel Pipeline",
        steps=[],
    )

    step = WorkflowStep.create(
        name="Download video",
        capability="video_download",
    )

    workflow.add_step(step)

    assert workflow.steps == [step]

def test_published_workflow_cannot_add_step():
    workflow = Workflow.create(
        name="AutoReel Pipeline",
        steps=[
            WorkflowStep.create(
                name="Download video",
                capability="video_download",
            )
        ],
    )

    workflow.publish()

    new_step = WorkflowStep.create(
        name="Transcribe",
        capability="transcription",
    )

    with pytest.raises(ValueError):
        workflow.add_step(new_step)

def test_workflow_step_is_immutable():
    step = WorkflowStep.create(
        name="Download video",
        capability="video_download",
    )

    with pytest.raises(FrozenInstanceError):
        step.name = "Something else"