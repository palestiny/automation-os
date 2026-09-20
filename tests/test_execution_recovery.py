from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.application.execution_recovery import (
    ExecutionRecoveryPolicy,
    RecoverStaleExecution,
)
from app.domain.execution import Execution, ExecutionState
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository


NOW = datetime(2026, 1, 1, 12, 0, 0)


def running_execution(started_at: datetime = NOW - timedelta(minutes=31)) -> Execution:
    return Execution(
        id=uuid4(),
        workflow_id=uuid4(),
        current_step=0,
        state=ExecutionState.RUNNING,
        attempt=1,
        started_at=started_at,
    )


def test_recover_stale_running_execution_marks_it_failed():
    repository = InMemoryExecutionRepository()
    execution = running_execution()
    repository.save(execution)

    use_case = RecoverStaleExecution(
        repository,
        ExecutionRecoveryPolicy(stale_after=timedelta(minutes=30)),
    )

    result = use_case.execute(execution.id, now=NOW)

    assert result is not None
    assert result.state is ExecutionState.FAILED
    assert result.events[-1].event_type == "execution.recovered_stale"


def test_non_stale_running_execution_is_not_recovered():
    repository = InMemoryExecutionRepository()
    execution = running_execution(started_at=NOW - timedelta(minutes=29))
    repository.save(execution)

    use_case = RecoverStaleExecution(
        repository,
        ExecutionRecoveryPolicy(stale_after=timedelta(minutes=30)),
    )

    result = use_case.execute(execution.id, now=NOW)

    assert result is None
    assert repository.get(execution.id).state is ExecutionState.RUNNING


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.CREATED,
        ExecutionState.WAITING,
        ExecutionState.RETRYING,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    ],
)
def test_recovery_does_not_change_non_running_states(state):
    repository = InMemoryExecutionRepository()
    execution = Execution(
        id=uuid4(),
        workflow_id=uuid4(),
        current_step=0,
        state=state,
        attempt=1,
    )
    repository.save(execution)

    use_case = RecoverStaleExecution(
        repository,
        ExecutionRecoveryPolicy(stale_after=timedelta(minutes=30)),
    )

    assert use_case.execute(execution.id, now=NOW) is None
    assert repository.get(execution.id).state is state


def test_recovery_is_idempotent_after_first_recovery():
    repository = InMemoryExecutionRepository()
    execution = running_execution()
    repository.save(execution)

    use_case = RecoverStaleExecution(
        repository,
        ExecutionRecoveryPolicy(stale_after=timedelta(minutes=30)),
    )

    first = use_case.execute(execution.id, now=NOW)
    second = use_case.execute(execution.id, now=NOW)

    assert first.id == execution.id
    assert second is None
    assert len(execution.events) == 1


def test_recovery_does_not_execute_workflow_or_create_new_execution():
    repository = InMemoryExecutionRepository()
    execution = running_execution()
    repository.save(execution)

    use_case = RecoverStaleExecution(
        repository,
        ExecutionRecoveryPolicy(stale_after=timedelta(minutes=30)),
    )

    result = use_case.execute(execution.id, now=NOW)

    assert result.id == execution.id
    assert len(repository.all()) == 1


def test_missing_execution_is_rejected():
    use_case = RecoverStaleExecution(
        InMemoryExecutionRepository(),
        ExecutionRecoveryPolicy(stale_after=timedelta(minutes=30)),
    )

    with pytest.raises(ValueError, match="Execution not found"):
        use_case.execute(uuid4(), now=NOW)

def test_recovery_policy_rejects_non_positive_timeout():
    with pytest.raises(ValueError, match="greater than zero"):
        ExecutionRecoveryPolicy(stale_after=timedelta(0))


def test_batch_recovery_is_deterministic_and_sequential():
    repository = InMemoryExecutionRepository()
    first = running_execution()
    second = running_execution()
    repository.save(second)
    repository.save(first)

    recovery = RecoverStaleExecution(
        repository,
        ExecutionRecoveryPolicy(stale_after=timedelta(minutes=30)),
    )
    batch = __import__("app.application.execution_recovery", fromlist=["RecoverStaleExecutions"]).RecoverStaleExecutions(
        repository,
        recovery,
    )

    results = batch.execute(now=NOW)

    assert tuple(item.id for item in results) == tuple(
        sorted((first.id, second.id), key=str)
    )
    assert all(item.state is ExecutionState.FAILED for item in results)


def test_conditional_persistence_does_not_overwrite_newer_state():
    repository = InMemoryExecutionRepository()
    execution = running_execution()
    repository.save(execution)

    replacement = Execution(
        id=execution.id,
        workflow_id=execution.workflow_id,
        current_step=execution.current_step,
        state=ExecutionState.CANCELLED,
        attempt=execution.attempt,
        started_at=execution.started_at,
    )

    assert repository.save_if_state(replacement, ExecutionState.RUNNING) is True
    stale_copy = running_execution(started_at=execution.started_at)
    stale_copy.id = execution.id
    assert repository.save_if_state(stale_copy, ExecutionState.RUNNING) is False
    assert repository.get(execution.id).state is ExecutionState.CANCELLED
