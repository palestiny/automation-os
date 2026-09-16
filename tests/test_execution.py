from uuid import uuid4
import pytest
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.execution_step import ExecutionStepState


def test_execution_starts_successfully():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()

    assert execution.state == ExecutionState.RUNNING
    assert execution.started_at is not None


def test_execution_started_at_is_preserved_across_execution_retry():
    execution = Execution.create(workflow_id=uuid4())

    execution.start()
    first_started_at = execution.started_at

    execution.fail()
    execution.retry()
    execution.start()

    assert execution.started_at == first_started_at


def test_execution_cannot_start_twice():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()

    with pytest.raises(ValueError):
        execution.start()


def test_execution_completes_current_step():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()

    assert execution.current_step == 0

    execution.complete_step()

    assert execution.current_step == 1
    assert execution.state == ExecutionState.RUNNING


def test_execution_cannot_complete_step_before_start():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    with pytest.raises(ValueError):
        execution.complete_step()


def test_execution_can_wait_when_running():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()
    execution.wait()

    assert execution.state == ExecutionState.WAITING


def test_execution_cannot_wait_before_start():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    with pytest.raises(ValueError):
        execution.wait()


def test_execution_can_resume_when_waiting():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()
    execution.wait()
    execution.resume()

    assert execution.state == ExecutionState.RUNNING


def test_execution_cannot_resume_when_not_waiting():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    with pytest.raises(ValueError):
        execution.resume()


def test_execution_can_be_completed_when_running():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()
    execution.complete()

    assert execution.state == ExecutionState.COMPLETED
    assert execution.finished_at is not None


def test_execution_cannot_complete_when_not_running():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    with pytest.raises(ValueError):
        execution.complete()


def test_execution_can_fail_when_running():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()
    execution.fail()

    assert execution.state == ExecutionState.FAILED
    assert execution.finished_at is None


def test_execution_cannot_fail_when_not_running():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    with pytest.raises(ValueError):
        execution.fail()


def test_execution_can_retry_when_failed():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()
    execution.fail()
    execution.retry()

    assert execution.state == ExecutionState.RETRYING


def test_execution_cannot_retry_when_not_failed():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    with pytest.raises(ValueError):
        execution.retry()


def test_execution_can_be_cancelled_when_running():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()
    execution.cancel()

    assert execution.state == ExecutionState.CANCELLED
    assert execution.finished_at is not None


def test_execution_can_be_cancelled_when_created():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.cancel()

    assert execution.state == ExecutionState.CANCELLED
    assert execution.finished_at is not None


def test_execution_can_be_cancelled_when_waiting():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()
    execution.wait()
    execution.cancel()

    assert execution.state == ExecutionState.CANCELLED
    assert execution.finished_at is not None


def test_execution_cannot_cancel_when_failed():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()
    execution.fail()

    with pytest.raises(ValueError):
        execution.cancel()


def test_execution_cannot_cancel_when_completed():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()
    execution.complete()

    with pytest.raises(ValueError):
        execution.cancel()


def test_execution_cannot_cancel_when_already_cancelled():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.cancel()

    with pytest.raises(ValueError):
        execution.cancel()


def test_execution_starts_with_first_attempt():
    execution = Execution.create(workflow_id=uuid4())

    assert execution.attempt == 1


def test_execution_retry_increments_attempt():
    execution = Execution.create(workflow_id=uuid4())

    execution.start()
    execution.fail()
    execution.retry()

    assert execution.attempt == 2
    assert execution.state == ExecutionState.RETRYING


def test_execution_can_start_after_retry():
    execution = Execution.create(workflow_id=uuid4())

    execution.start()
    execution.fail()
    execution.retry()

    assert execution.state == ExecutionState.RETRYING

    execution.start()

    assert execution.state == ExecutionState.RUNNING


def test_execution_retry_does_not_start_execution():
    execution = Execution.create(workflow_id=uuid4())

    execution.start()
    execution.fail()
    execution.retry()

    assert execution.state == ExecutionState.RETRYING


def test_execution_creates_execution_steps_from_workflow():
    step1 = WorkflowStep.create(
        name="Download",
        capability="video_download",
    )

    step2 = WorkflowStep.create(
        name="Transcribe",
        capability="transcribe",
    )

    workflow = Workflow.create(
        name="Video Processing",
        steps=[step1, step2],
    )

    execution = Execution.create_from_workflow(workflow)

    assert len(execution.steps) == 2
    assert execution.steps[0].workflow_step_id == step1.id
    assert execution.steps[1].workflow_step_id == step2.id


def test_execution_start_starts_current_execution_step():
    step = WorkflowStep.create(
        name="Download",
        capability="video_download",
    )

    workflow = Workflow.create(
        name="Video Processing",
        steps=[step],
    )

    execution = Execution.create_from_workflow(workflow)

    execution.start()

    assert execution.state == ExecutionState.RUNNING
    assert execution.steps[0].state == ExecutionStepState.RUNNING


def test_execution_complete_step_completes_current_execution_step():
    step = WorkflowStep.create(
        name="Download",
        capability="video_download",
    )

    workflow = Workflow.create(
        name="Video Processing",
        steps=[step],
    )

    execution = Execution.create_from_workflow(workflow)

    execution.start()
    execution.complete_step()

    assert execution.steps[0].state == ExecutionStepState.COMPLETED
    assert execution.current_step == 1


def test_execution_step_retry_does_not_increment_execution_attempt():
    step = WorkflowStep.create(
        name="Download",
        capability="video_download",
    )
    workflow = Workflow.create(
        name="Video Processing",
        steps=[step],
    )

    execution = Execution.create_from_workflow(workflow)
    execution.start()

    execution.fail_current_step()
    execution.retry_current_step()

    assert execution.attempt == 1
    assert execution.steps[0].attempt == 2
    assert execution.steps[0].state == ExecutionStepState.RUNNING
    assert execution.state == ExecutionState.RUNNING


def test_execution_can_fail_current_step_without_failing_execution():
    step = WorkflowStep.create(
        name="Download",
        capability="video_download",
    )
    workflow = Workflow.create(
        name="Video Processing",
        steps=[step],
    )

    execution = Execution.create_from_workflow(workflow)
    execution.start()

    execution.fail_current_step()

    assert execution.steps[0].state == ExecutionStepState.FAILED
    assert execution.state == ExecutionState.RUNNING
