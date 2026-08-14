from uuid import uuid4

import pytest

from app.domain.execution import Execution, ExecutionState


def test_execution_starts_successfully():
    workflow_id = uuid4()

    execution = Execution.create(workflow_id)

    execution.start()

    assert execution.state == ExecutionState.RUNNING
    assert execution.started_at is not None


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

    assert execution.state == ExecutionState.RUNNING

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