from uuid import uuid4

import pytest

from app.application.cancel_execution import CancelExecution
from app.domain.execution import Execution, ExecutionState
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository


def build_execution(state: ExecutionState) -> Execution:
    execution = Execution.create(uuid4())
    if state is ExecutionState.CREATED:
        return execution
    execution.start()
    if state is ExecutionState.RUNNING:
        return execution
    if state is ExecutionState.WAITING:
        execution.wait()
        return execution
    if state is ExecutionState.COMPLETED:
        execution.complete()
        return execution
    if state is ExecutionState.FAILED:
        execution.fail()
        return execution
    if state is ExecutionState.RETRYING:
        execution.fail()
        execution.retry()
        return execution
    if state is ExecutionState.CANCELLED:
        execution.cancel()
        return execution
    raise AssertionError(f"Unsupported state: {state}")


@pytest.mark.parametrize(
    "state",
    [ExecutionState.CREATED, ExecutionState.RUNNING, ExecutionState.WAITING],
)
def test_cancel_execution_persists_cancelled_execution(state):
    repository = InMemoryExecutionRepository()
    execution = build_execution(state)
    repository.save(execution)

    result = CancelExecution(repository).execute(execution.id)

    assert result is execution
    assert result.state is ExecutionState.CANCELLED
    assert result.finished_at is not None
    assert repository.get(execution.id) is execution


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.RETRYING,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    ],
)
def test_cancel_execution_rejects_domain_invalid_states(state):
    repository = InMemoryExecutionRepository()
    execution = build_execution(state)
    repository.save(execution)

    with pytest.raises(ValueError, match="cancelled|cancel"):
        CancelExecution(repository).execute(execution.id)

    assert repository.get(execution.id) is execution
    assert execution.state is state


def test_cancel_execution_rejects_missing_execution():
    repository = InMemoryExecutionRepository()

    with pytest.raises(ValueError, match="Execution not found"):
        CancelExecution(repository).execute(uuid4())
