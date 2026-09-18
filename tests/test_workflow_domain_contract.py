import pytest

from app.domain.workflow import Workflow, WorkflowState, WorkflowStep


def test_workflow_step_requires_name_and_capability():
    with pytest.raises(ValueError):
        WorkflowStep.create(name="", capability="video_download")

    with pytest.raises(ValueError):
        WorkflowStep.create(name="Download", capability="")


def test_workflow_steps_are_typed_domain_objects():
    step = WorkflowStep.create(name="Download", capability="video_download")
    workflow = Workflow.create(name="Content", steps=[step])

    assert workflow.steps == [step]
    assert workflow.state is WorkflowState.DRAFT


def test_published_workflow_cannot_be_modified():
    step = WorkflowStep.create(name="Download", capability="video_download")
    workflow = Workflow.create(name="Content", steps=[step])
    workflow.publish()

    with pytest.raises(ValueError):
        workflow.add_step(
            WorkflowStep.create(name="Transcribe", capability="transcribe")
        )


def test_publish_requires_at_least_one_step():
    workflow = Workflow.create(name="Empty", steps=[])

    with pytest.raises(ValueError):
        workflow.publish()
