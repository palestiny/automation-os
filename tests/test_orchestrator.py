from app.domain.workflow import Workflow, WorkflowStep
from app.application.orchestrator import Orchestrator
import pytest

def test_orchestrator_starts_workflow():
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

    orchestrator = Orchestrator()

    execution = orchestrator.start(workflow)

    assert execution.state.value == "running"
    assert execution.current_step == 0

def test_orchestrator_cannot_start_draft_workflow():
    workflow = Workflow.create(
        name="AutoReel Pipeline",
        steps=[
            WorkflowStep.create(
                name="Download video",
                capability="video_download",
            )
        ],
    )

    orchestrator = Orchestrator()

    with pytest.raises(ValueError):
        orchestrator.start(workflow)