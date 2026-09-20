from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.application.execution_metrics import GetExecutionMetrics
from app.domain.execution import Execution, ExecutionState
from app.domain.execution_event import ExecutionEvent
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionHistoryRepository,
    InMemoryExecutionRepository,
)


WINDOW_START = datetime(2026, 1, 1, 10, 0, 0)
WINDOW_END = datetime(2026, 1, 1, 12, 0, 0)


def make_execution(
    *,
    state: ExecutionState,
    started_at: datetime | None,
    finished_at: datetime | None,
    attempt: int = 1,
    workflow_id=None,
    workflow_version_id=None,
) -> Execution:
    return Execution(
        id=uuid4(),
        workflow_id=workflow_id or uuid4(),
        workflow_version_id=workflow_version_id,
        current_step=1,
        state=state,
        attempt=attempt,
        started_at=started_at,
        finished_at=finished_at,
    )


def add_event(
    history: InMemoryExecutionHistoryRepository,
    execution: Execution,
    sequence: int,
    event_type: str,
    occurred_at: datetime,
) -> None:
    history.append(
        ExecutionEvent(
            execution_id=execution.id,
            workflow_id=execution.workflow_id,
            sequence=sequence,
            event_type=event_type,
            state=execution.state,
            attempt=execution.attempt,
            occurred_at=occurred_at,
        )
    )


def test_empty_window_returns_zero_metrics():
    metrics = GetExecutionMetrics(
        InMemoryExecutionRepository(),
        InMemoryExecutionHistoryRepository(),
    )

    result = metrics.execute(WINDOW_START, WINDOW_END)

    assert result.total_executions == 0
    assert result.state_counts == {state.value: 0 for state in ExecutionState}
    assert result.completed_duration_seconds is None
    assert result.retry_count == 0
    assert result.recovery_count == 0
    assert result.workflow_breakdown == {}
    assert result.workflow_version_breakdown == {}


def test_metrics_filter_by_started_at_and_count_states():
    executions = InMemoryExecutionRepository()
    history = InMemoryExecutionHistoryRepository()
    workflow_id = uuid4()

    included_completed = make_execution(
        state=ExecutionState.COMPLETED,
        started_at=WINDOW_START + timedelta(minutes=5),
        finished_at=WINDOW_START + timedelta(minutes=15),
        workflow_id=workflow_id,
    )
    included_failed = make_execution(
        state=ExecutionState.FAILED,
        started_at=WINDOW_START + timedelta(minutes=20),
        finished_at=None,
        workflow_id=workflow_id,
    )
    excluded = make_execution(
        state=ExecutionState.COMPLETED,
        started_at=WINDOW_END + timedelta(minutes=1),
        finished_at=WINDOW_END + timedelta(minutes=2),
        workflow_id=workflow_id,
    )
    for execution in (included_completed, included_failed, excluded):
        executions.save(execution)

    result = GetExecutionMetrics(executions, history).execute(
        WINDOW_START, WINDOW_END
    )

    assert result.total_executions == 2
    assert result.state_counts["completed"] == 1
    assert result.state_counts["failed"] == 1
    assert result.state_counts["created"] == 0


def test_duration_statistics_include_only_completed_executions_with_timestamps():
    executions = InMemoryExecutionRepository()
    history = InMemoryExecutionHistoryRepository()

    first = make_execution(
        state=ExecutionState.COMPLETED,
        started_at=WINDOW_START,
        finished_at=WINDOW_START + timedelta(seconds=30),
    )
    second = make_execution(
        state=ExecutionState.COMPLETED,
        started_at=WINDOW_START + timedelta(minutes=1),
        finished_at=WINDOW_START + timedelta(minutes=2),
    )
    incomplete = make_execution(
        state=ExecutionState.RUNNING,
        started_at=WINDOW_START + timedelta(minutes=3),
        finished_at=None,
    )
    for execution in (first, second, incomplete):
        executions.save(execution)

    result = GetExecutionMetrics(executions, history).execute(
        WINDOW_START, WINDOW_END
    )

    assert result.completed_duration_seconds == {
        "count": 2,
        "total": 90.0,
        "average": 45.0,
        "minimum": 30.0,
        "maximum": 60.0,
    }


def test_retry_and_recovery_counts_are_lifecycle_event_counts():
    executions = InMemoryExecutionRepository()
    history = InMemoryExecutionHistoryRepository()
    execution = make_execution(
        state=ExecutionState.FAILED,
        started_at=WINDOW_START + timedelta(minutes=5),
        finished_at=None,
        attempt=2,
    )
    executions.save(execution)
    add_event(history, execution, 1, "execution.started", WINDOW_START + timedelta(minutes=5))
    add_event(history, execution, 2, "execution.failed", WINDOW_START + timedelta(minutes=6))
    add_event(history, execution, 3, "execution.retrying", WINDOW_START + timedelta(minutes=7))
    add_event(history, execution, 4, "execution.recovered_stale", WINDOW_START + timedelta(minutes=8))

    result = GetExecutionMetrics(executions, history).execute(
        WINDOW_START, WINDOW_END
    )

    assert result.retry_count == 1
    assert result.recovery_count == 1


def test_workflow_and_version_breakdowns_include_legacy_unversioned_bucket():
    executions = InMemoryExecutionRepository()
    history = InMemoryExecutionHistoryRepository()
    workflow_id = uuid4()
    version_id = uuid4()

    versioned = make_execution(
        state=ExecutionState.COMPLETED,
        started_at=WINDOW_START + timedelta(minutes=1),
        finished_at=WINDOW_START + timedelta(minutes=2),
        workflow_id=workflow_id,
        workflow_version_id=version_id,
    )
    legacy = make_execution(
        state=ExecutionState.COMPLETED,
        started_at=WINDOW_START + timedelta(minutes=3),
        finished_at=WINDOW_START + timedelta(minutes=4),
        workflow_id=workflow_id,
    )
    executions.save(versioned)
    executions.save(legacy)

    result = GetExecutionMetrics(executions, history).execute(
        WINDOW_START, WINDOW_END
    )

    assert result.workflow_breakdown == {str(workflow_id): 2}
    assert result.workflow_version_breakdown == {
        str(version_id): 1,
        "unversioned": 1,
    }


def test_attempt_distribution_is_deterministic():
    executions = InMemoryExecutionRepository()
    history = InMemoryExecutionHistoryRepository()

    for attempt in (2, 1, 2):
        executions.save(
            make_execution(
                state=ExecutionState.COMPLETED,
                started_at=WINDOW_START + timedelta(minutes=attempt),
                finished_at=WINDOW_START + timedelta(minutes=attempt, seconds=1),
                attempt=attempt,
            )
        )

    result = GetExecutionMetrics(executions, history).execute(
        WINDOW_START, WINDOW_END
    )

    assert result.attempt_distribution == {1: 1, 2: 2}


def test_metrics_are_read_only_and_repeatable():
    executions = InMemoryExecutionRepository()
    history = InMemoryExecutionHistoryRepository()
    execution = make_execution(
        state=ExecutionState.COMPLETED,
        started_at=WINDOW_START,
        finished_at=WINDOW_START + timedelta(seconds=10),
    )
    executions.save(execution)

    metrics = GetExecutionMetrics(executions, history)
    first = metrics.execute(WINDOW_START, WINDOW_END)
    second = metrics.execute(WINDOW_START, WINDOW_END)

    assert first == second
    persisted = executions.get(execution.id)
    assert persisted.state is ExecutionState.COMPLETED
    assert persisted.events == ()
    assert history.list(execution.id) == ()


def test_invalid_window_is_rejected():
    metrics = GetExecutionMetrics(
        InMemoryExecutionRepository(),
        InMemoryExecutionHistoryRepository(),
    )

    with pytest.raises(ValueError, match="window_start must be before window_end"):
        metrics.execute(WINDOW_END, WINDOW_START)
