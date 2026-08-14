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