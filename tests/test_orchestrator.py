from app.application.capability_result import CapabilityResult
from app.application.errors import NetworkTimeoutError
from app.application.orchestrator import Orchestrator
from app.application.retry_policy import RetryPolicy
from app.domain.workflow import Workflow, WorkflowStep
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
    orchestrator = Orchestrator(dispatcher, RetryPolicy())

    execution = orchestrator.start(workflow)

    assert execution.state.value == "completed"
    assert execution.current_step == 1
    assert execution.attempt == 1
    assert execution.steps[0].attempt == 1


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

    orchestrator = Orchestrator(FakeCapabilityDispatcher(), RetryPolicy())

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
    orchestrator = Orchestrator(dispatcher, RetryPolicy())

    execution = orchestrator.start(workflow)

    assert dispatcher.dispatched_capability_id == "video_download"
    assert execution.current_step == 1


class FailingCapabilityDispatcher:
    def dispatch(self, capability_id, context):
        return CapabilityResult.failure(Exception("Network timeout"))


def test_orchestrator_fails_execution_when_capability_fails():
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

    execution = Orchestrator(
        FailingCapabilityDispatcher(),
        RetryPolicy(),
    ).start(workflow)

    assert execution.state.value == "failed"
    assert execution.steps[0].state.value == "failed"
    assert execution.attempt == 1
    assert execution.steps[0].attempt == 1


class RetryableFailingCapabilityDispatcher:
    def dispatch(self, capability_id, context):
        return CapabilityResult.failure(
            NetworkTimeoutError("Network timeout")
        )


def test_orchestrator_exhausts_step_retries_without_incrementing_execution_attempt():
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

    execution = Orchestrator(
        RetryableFailingCapabilityDispatcher(),
        RetryPolicy(),
    ).start(workflow)

    assert execution.state.value == "failed"
    assert execution.attempt == 1
    assert execution.steps[0].attempt == 3


class MultiStepCapabilityDispatcher:
    def __init__(self):
        self.dispatched_capabilities = []

    def dispatch(self, capability_id, context):
        self.dispatched_capabilities.append(capability_id)
        return CapabilityResult.success()


def test_orchestrator_executes_all_workflow_steps():
    workflow = Workflow.create(
        name="AutoReel Pipeline",
        steps=[
            WorkflowStep.create(
                name="Download video",
                capability="video_download",
            ),
            WorkflowStep.create(
                name="Transcribe video",
                capability="transcribe",
            ),
            WorkflowStep.create(
                name="Create clip",
                capability="create_clip",
            ),
        ],
    )
    workflow.publish()

    dispatcher = MultiStepCapabilityDispatcher()
    execution = Orchestrator(dispatcher, RetryPolicy()).start(workflow)

    assert dispatcher.dispatched_capabilities == [
        "video_download",
        "transcribe",
        "create_clip",
    ]
    assert execution.current_step == 3
    assert execution.state.value == "completed"
    assert execution.attempt == 1
    assert [step.attempt for step in execution.steps] == [1, 1, 1]


class FailOnceCapabilityDispatcher:
    def __init__(self):
        self.calls = 0

    def dispatch(self, capability_id, context):
        self.calls += 1
        if self.calls == 1:
            return CapabilityResult.failure(
                NetworkTimeoutError("Network timeout")
            )
        return CapabilityResult.success()


def test_orchestrator_retries_failed_step_and_succeeds():
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

    dispatcher = FailOnceCapabilityDispatcher()
    execution = Orchestrator(dispatcher, RetryPolicy()).start(workflow)

    assert dispatcher.calls == 2
    assert execution.attempt == 1
    assert execution.steps[0].attempt == 2
    assert execution.current_step == 1
    assert execution.state.value == "completed"


class FailMiddleStepOnceDispatcher:
    def __init__(self):
        self.calls = []
        self.middle_step_attempts = 0

    def dispatch(self, capability_id, context):
        self.calls.append(capability_id)
        if capability_id == "transcribe":
            self.middle_step_attempts += 1
            if self.middle_step_attempts == 1:
                return CapabilityResult.failure(
                    NetworkTimeoutError("Network timeout")
                )
        return CapabilityResult.success()


def test_orchestrator_retries_only_failed_step_in_multi_step_workflow():
    workflow = Workflow.create(
        name="AutoReel Pipeline",
        steps=[
            WorkflowStep.create(
                name="Download video",
                capability="video_download",
            ),
            WorkflowStep.create(
                name="Transcribe video",
                capability="transcribe",
            ),
            WorkflowStep.create(
                name="Create clip",
                capability="create_clip",
            ),
        ],
    )
    workflow.publish()

    dispatcher = FailMiddleStepOnceDispatcher()
    execution = Orchestrator(dispatcher, RetryPolicy()).start(workflow)

    assert dispatcher.calls == [
        "video_download",
        "transcribe",
        "transcribe",
        "create_clip",
    ]
    assert execution.current_step == 3
    assert execution.state.value == "completed"
    assert execution.attempt == 1
    assert [step.attempt for step in execution.steps] == [1, 2, 1]
