from uuid import uuid4

import pytest

from app.application.retry_execution import RetryExecution
from app.domain.execution import Execution, ExecutionState
from app.domain.retry_policy import RetryPolicy
from app.application.retry_execution import ManualRetryContext
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository


def failed_execution() -> Execution:
    execution = Execution.create(uuid4())
    execution.start()
    execution.fail()
    return execution


def test_retry_execution_persists_retrying_execution_and_increments_attempt():
    executions = InMemoryExecutionRepository()
    execution = failed_execution()
    executions.save(execution)

    use_case = RetryExecution(executions)

    result = use_case.execute(execution.id)

    assert result is execution
    assert result.state is ExecutionState.RETRYING
    assert result.attempt == 2
    assert executions.get(execution.id) is execution


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.CREATED,
        ExecutionState.RUNNING,
        ExecutionState.WAITING,
        ExecutionState.RETRYING,
        ExecutionState.COMPLETED,
        ExecutionState.CANCELLED,
    ],
)
def test_retry_execution_rejects_invalid_states(state):
    execution = Execution(
        id=uuid4(),
        workflow_id=uuid4(),
        current_step=0,
        state=state,
        attempt=1,
    )
    executions = InMemoryExecutionRepository()
    executions.save(execution)

    use_case = RetryExecution(executions)

    with pytest.raises(ValueError, match="retry"):
        use_case.execute(execution.id)

    assert execution.state is state
    assert execution.attempt == 1


def test_retry_execution_rejects_missing_execution():
    executions = InMemoryExecutionRepository()
    use_case = RetryExecution(executions)

    with pytest.raises(ValueError, match="Execution not found"):
        use_case.execute(uuid4())



def test_retry_execution_enforces_policy_when_configured():
    executions = InMemoryExecutionRepository()
    execution = failed_execution()
    execution.attempt = 3
    executions.save(execution)

    use_case = RetryExecution(
        executions,
        retry_policy=RetryPolicy(max_attempts=3),
    )

    with pytest.raises(ValueError, match="RetryPolicy"):
        use_case.execute(execution.id)

    assert execution.state is ExecutionState.FAILED
    assert execution.attempt == 3


def test_manual_retry_can_override_policy_only_with_authorization_and_context():
    executions = InMemoryExecutionRepository()
    execution = failed_execution()
    execution.attempt = 3
    executions.save(execution)
    calls = []

    def authorize(target, context):
        calls.append((target.id, context.actor_id, context.reason))

    use_case = RetryExecution(
        executions,
        retry_policy=RetryPolicy(max_attempts=3),
        manual_authorizer=authorize,
    )

    context = ManualRetryContext(actor_id="operator-1", reason="Recover after verified transient outage")
    result = use_case.execute(execution.id, manual_context=context)

    assert result.state is ExecutionState.RETRYING
    assert result.attempt == 4
    assert calls == [(execution.id, "operator-1", "Recover after verified transient outage")]


def test_manual_retry_override_requires_authorization():
    executions = InMemoryExecutionRepository()
    execution = failed_execution()
    execution.attempt = 3
    executions.save(execution)

    use_case = RetryExecution(
        executions,
        retry_policy=RetryPolicy(max_attempts=3),
    )

    with pytest.raises(PermissionError, match="authorization"):
        use_case.execute(
            execution.id,
            manual_context=ManualRetryContext(
                actor_id="operator-1",
                reason="Emergency recovery",
            ),
        )
