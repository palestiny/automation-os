from app.domain.workflow import Workflow, WorkflowStep
from app.application.orchestrator import Orchestrator
from app.application.capability_result import CapabilityResult
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

    dispatcher = FakeCapabilityDispatcher()
    orchestrator = Orchestrator(dispatcher)

    execution = orchestrator.start(workflow)

    assert execution.state.value == "running"
    assert execution.current_step == 1

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
    dispatcher = FakeCapabilityDispatcher()
    orchestrator = Orchestrator(dispatcher)

    with pytest.raises(ValueError):
        orchestrator.start(workflow)

class FakeCapabilityDispatcher:
    def __init__(self):
        self.dispatched_capability_id = None
        self.dispatched_context = None

    def dispatch(self, capability_id, context):
        self.dispatched_capability_id = capability_id
        self.dispatched_context = context

        return CapabilityResult.success()

def test_orchestrator_dispatches_current_workflow_step():
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

    dispatcher = FakeCapabilityDispatcher()
    orchestrator = Orchestrator(dispatcher)

    execution = orchestrator.start(workflow)

    assert dispatcher.dispatched_capability_id == "video_download"
    assert execution.current_step == 1