from uuid import uuid4

import pytest

from app.application.resume_execution import ResumeExecution
from app.domain.execution import Execution, ExecutionState
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository


def build_waiting_execution() -> Execution:
    execution = Execution.create(uuid4())
    execution.start()
    execution.wait()
    return execution


def test_resume_execution_persists_running_execution():
    repository = InMemoryExecutionRepository()
    execution = build_waiting_execution()
    repository.save(execution)

    result = ResumeExecution(repository).execute(execution.id)

    assert result is execution
    assert result.state is ExecutionState.RUNNING
    assert repository.get(execution.id) is execution


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.CREATED,
        ExecutionState.RUNNING,
        ExecutionState.RETRYING,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    ],
)
def test_resume_execution_rejects_non_waiting_states(state):
    repository = InMemoryExecutionRepository()
    execution = Execution.create(uuid4())

    if state is ExecutionState.CREATED:
        pass
    elif state is ExecutionState.RUNNING:
        execution.start()
    elif state is ExecutionState.RETRYING:
        execution.start()
        execution.fail()
        execution.retry()
    elif state is ExecutionState.COMPLETED:
        execution.start()
        execution.complete()
    elif state is ExecutionState.FAILED:
        execution.start()
        execution.fail()
    elif state is ExecutionState.CANCELLED:
        execution.cancel()

    repository.save(execution)

    with pytest.raises(ValueError, match="resume|WAITING"):
        ResumeExecution(repository).execute(execution.id)

    assert repository.get(execution.id) is execution
    assert execution.state is state


def test_resume_execution_rejects_missing_execution():
    repository = InMemoryExecutionRepository()

    with pytest.raises(ValueError, match="Execution not found"):
        ResumeExecution(repository).execute(uuid4())
