from dataclasses import FrozenInstanceError

import pytest

from app.domain.workflow import Workflow, WorkflowStep, WorkflowState


def make_step(name="Download video", capability="video_download"):
    return WorkflowStep.create(name=name, capability=capability)


def test_workflow_can_be_created():
    workflow = Workflow.create(
        name="Content Pipeline",
        steps=[],
    )

    assert workflow.name == "Content Pipeline"
    assert workflow.steps == []


def test_workflow_is_created_as_draft():
    workflow = Workflow.create(
        name="Content Pipeline",
        steps=[],
    )

    assert workflow.state == WorkflowState.DRAFT


def test_workflow_can_be_published():
    workflow = Workflow.create(
        name="Content Pipeline",
        steps=[make_step()],
    )

    workflow.publish()

    assert workflow.state == WorkflowState.PUBLISHED


def test_workflow_cannot_be_published_twice():
    workflow = Workflow.create(
        name="Content Pipeline",
        steps=[make_step()],
    )

    workflow.publish()

    with pytest.raises(ValueError):
        workflow.publish()


def test_workflow_cannot_be_published_without_steps():
    workflow = Workflow.create(
        name="Content Pipeline",
        steps=[],
    )

    with pytest.raises(ValueError):
        workflow.publish()


def test_workflow_name_cannot_be_blank():
    with pytest.raises(ValueError):
        Workflow.create(name="   ", steps=[])


def test_workflow_step_can_be_created():
    step = WorkflowStep.create(
        name="Download video",
        capability="video_download",
    )

    assert step.name == "Download video"
    assert step.capability == "video_download"


def test_workflow_step_name_cannot_be_blank():
    with pytest.raises(ValueError):
        WorkflowStep.create(name="   ", capability="video_download")


def test_workflow_step_capability_cannot_be_blank():
    with pytest.raises(ValueError):
        WorkflowStep.create(name="Download video", capability="   ")


def test_workflow_can_add_step():
    workflow = Workflow.create(
        name="Content Pipeline",
        steps=[],
    )

    step = make_step()
    workflow.add_step(step)

    assert workflow.steps == [step]


def test_published_workflow_cannot_add_step():
    workflow = Workflow.create(
        name="Content Pipeline",
        steps=[make_step()],
    )

    workflow.publish()

    new_step = WorkflowStep.create(
        name="Transcribe",
        capability="transcription",
    )

    with pytest.raises(ValueError):
        workflow.add_step(new_step)


def test_published_workflow_cannot_be_mutated_through_steps_collection():
    workflow = Workflow.create(
        name="Content Pipeline",
        steps=[make_step()],
    )

    workflow.publish()

    exposed_steps = workflow.steps
    exposed_steps.append(make_step("Transcribe", "transcription"))

    assert len(workflow.steps) == 1


def test_workflow_allows_duplicate_capabilities():
    first = make_step("Download source", "video_download")
    second = make_step("Download reference", "video_download")

    workflow = Workflow.create(
        name="Content Pipeline",
        steps=[first, second],
    )

    workflow.publish()

    assert workflow.steps == [first, second]


def test_workflow_step_is_immutable():
    step = make_step()

    with pytest.raises(FrozenInstanceError):
        step.name = "Something else"
