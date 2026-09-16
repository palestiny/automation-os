from app.domain.execution_step import ExecutionStep
import pytest

def test_execution_step_starts_with_first_attempt():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    assert step.attempt == 1

def test_execution_step_starts_in_created_state():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    assert step.state.value == "created"

def test_execution_step_can_start():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    step.start()

    assert step.state.value == "running"

def test_execution_step_cannot_start_if_not_created():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    step.start()

    with pytest.raises(ValueError):
        step.start()

def test_execution_step_can_complete():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    step.start()
    step.complete()
    assert step.state.value == "completed"

def test_execution_step_cannot_complete_if_not_running():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    with pytest.raises(ValueError):
        step.complete()

def test_execution_step_can_fail():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    step.start()
    step.fail()

    assert step.state.value == "failed"

def test_execution_step_can_retry_after_failure():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    step.start()
    step.fail()
    step.retry()

    assert step.state.value == "retrying"
    assert step.attempt == 2

def test_execution_step_can_start_after_retry():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    step.start()
    step.fail()
    step.retry()
    step.start()

    assert step.state.value == "running"

def test_execution_step_cannot_retry_if_not_failed():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    with pytest.raises(ValueError):
        step.retry()

def test_execution_step_cannot_retry_if_running():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    step.start()

    with pytest.raises(ValueError):
        step.retry()

def test_execution_step_cannot_retry_if_completed():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    step.start()
    step.complete()

    with pytest.raises(ValueError):
        step.retry()

def test_execution_step_can_retry_multiple_times():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    step.start()
    step.fail()
    step.retry()
    step.start()
    step.fail()
    step.retry()

    assert step.attempt == 3
    assert step.state.value == "retrying"