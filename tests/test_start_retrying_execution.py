from uuid import uuid4

import pytest

from app.application.start_retrying_execution import StartRetryingExecution
from app.domain.execution import Execution, ExecutionState
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository


def test_start_retrying_execution_persists_running_state():
    repository = InMemoryExecutionRepository()
    execution = Execution(
        id=uuid4(),
        workflow_id=uuid4(),
        current_step=2,
        state=ExecutionState.RETRYING,
        attempt=2,
    )
    repository.save(execution)

    result = StartRetryingExecution(repository).execute(execution.id)

    assert result is execution
    assert result.state is ExecutionState.RUNNING
    assert repository.get(execution.id).state is ExecutionState.RUNNING


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.CREATED,
        ExecutionState.RUNNING,
        ExecutionState.WAITING,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    ],
)
def test_start_retrying_execution_rejects_non_retrying_state(state):
    repository = InMemoryExecutionRepository()
    execution = Execution(
        id=uuid4(),
        workflow_id=uuid4(),
        current_step=0,
        state=state,
        attempt=1,
    )
    repository.save(execution)

    with pytest.raises(ValueError, match="CREATED|RETRYING"):
        StartRetryingExecution(repository).execute(execution.id)


def test_start_retrying_execution_rejects_missing_execution():
    repository = InMemoryExecutionRepository()

    with pytest.raises(ValueError, match="Execution not found"):
        StartRetryingExecution(repository).execute(uuid4())
