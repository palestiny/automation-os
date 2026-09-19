from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.start_workflow_execution import StartWorkflowExecution
from app.core.execution_dependencies import workflow_repository
from app.domain.execution import ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    EventRecordingExecutionRepository,
    InMemoryExecutionHistoryRepository,
    InMemoryExecutionIdempotencyRepository,
    InMemoryExecutionRepository,
)
from app.main import app


client = TestClient(app)


def published_workflow(name: str = "Pipeline") -> Workflow:
    workflow = Workflow.create(
        name,
        [WorkflowStep.create("Step 1", "test")],
    )
    workflow.publish()
    return workflow


def test_start_workflow_execution_is_idempotent_for_same_key():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflow_repository = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow()
    workflow_repository.save(workflow)

    idempotency = InMemoryExecutionIdempotencyRepository()
    start = StartWorkflowExecution(
        workflow_repository,
        executions,
        idempotency_repository=idempotency,
    )

    first = start.execute(workflow.id, idempotency_key="request-1")
    second = start.execute(workflow.id, idempotency_key="request-1")

    assert second is first
    assert len(executions.all()) == 1
    assert first.state is ExecutionState.RUNNING


def test_start_workflow_execution_rejects_idempotency_key_reuse_for_other_workflow():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    idempotency = InMemoryExecutionIdempotencyRepository()
    first_workflow = published_workflow("First")
    second_workflow = published_workflow("Second")
    workflows.save(first_workflow)
    workflows.save(second_workflow)

    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
    )

    start.execute(first_workflow.id, idempotency_key="request-1")

    with pytest.raises(ValueError, match="Idempotency key"):
        start.execute(second_workflow.id, idempotency_key="request-1")

    assert len(executions.all()) == 1


def test_execution_history_records_structured_start_event():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflows = InMemoryWorkflowRepository()
    inner_executions = InMemoryExecutionRepository()
    history = InMemoryExecutionHistoryRepository()
    executions = EventRecordingExecutionRepository(inner_executions, history)
    workflow = published_workflow()
    workflows.save(workflow)

    result = StartWorkflowExecution(workflows, executions).execute(workflow.id)

    entries = history.list(result.id)

    assert len(entries) == 1
    assert entries[0].event_type == "execution.started"
    assert entries[0].execution_id == result.id
    assert entries[0].workflow_id == workflow.id
    assert entries[0].state is ExecutionState.RUNNING
    assert entries[0].attempt == 1
    assert entries[0].sequence == 1


def test_execution_history_is_append_only_when_execution_is_saved_again():
    from app.domain.execution import Execution

    history = InMemoryExecutionHistoryRepository()
    inner_executions = InMemoryExecutionRepository()
    executions = EventRecordingExecutionRepository(inner_executions, history)
    execution = Execution.create(uuid4())

    execution.start()
    executions.save(execution)
    executions.save(execution)

    entries = history.list(execution.id)

    assert len(entries) == 1
    assert entries[0].sequence == 1


def test_api_replays_same_execution_for_duplicate_idempotency_key():
    workflow = published_workflow("API Idempotent Pipeline")
    workflow_repository.save(workflow)

    key = f"api-{uuid4()}"
    first = client.post(
        f"/executions/workflows/{workflow.id}",
        headers={"Idempotency-Key": key},
    )
    second = client.post(
        f"/executions/workflows/{workflow.id}",
        headers={"Idempotency-Key": key},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["execution_id"] == first.json()["execution_id"]


def test_api_rejects_idempotency_key_reuse_for_other_workflow():
    first_workflow = published_workflow("API First")
    second_workflow = published_workflow("API Second")
    workflow_repository.save(first_workflow)
    workflow_repository.save(second_workflow)

    key = f"api-conflict-{uuid4()}"
    first = client.post(
        f"/executions/workflows/{first_workflow.id}",
        headers={"Idempotency-Key": key},
    )
    second = client.post(
        f"/executions/workflows/{second_workflow.id}",
        headers={"Idempotency-Key": key},
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_execution_history_records_lifecycle_transitions_in_order():
    from app.domain.execution import Execution
    from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository

    history = InMemoryExecutionHistoryRepository()
    executions = EventRecordingExecutionRepository(
        InMemoryExecutionRepository(),
        history,
    )
    execution = Execution.create(uuid4())

    execution.start()
    executions.save(execution)
    execution.complete_step()
    executions.save(execution)
    execution.wait()
    executions.save(execution)
    execution.resume()
    executions.save(execution)
    execution.complete()
    executions.save(execution)

    assert [event.event_type for event in history.list(execution.id)] == [
        "execution.started",
        "execution.step_completed",
        "execution.waiting",
        "execution.resumed",
        "execution.completed",
    ]
    assert [event.sequence for event in history.list(execution.id)] == [1, 2, 3, 4, 5]


def test_start_without_idempotency_key_remains_non_idempotent():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    start = StartWorkflowExecution(workflows, executions)

    first = start.execute(workflow.id)
    second = start.execute(workflow.id)

    assert first.id != second.id
    assert len(executions.all()) == 2


def test_blank_idempotency_key_is_rejected():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=InMemoryExecutionIdempotencyRepository(),
    )

    with pytest.raises(ValueError, match="Idempotency key cannot be empty"):
        start.execute(workflow.id, idempotency_key="   ")


def test_history_persistence_failure_is_surfaced_without_second_state_authority():
    from app.domain.execution import Execution

    class FailingHistoryRepository:
        def append(self, event):
            raise RuntimeError("history unavailable")

        def list(self, execution_id):
            return ()

    inner = InMemoryExecutionRepository()
    executions = EventRecordingExecutionRepository(
        inner,
        FailingHistoryRepository(),
    )
    execution = Execution.create(uuid4())
    execution.start()

    with pytest.raises(RuntimeError, match="history unavailable"):
        executions.save(execution)

    assert inner.get(execution.id) is execution
    assert execution.state is ExecutionState.RUNNING


def test_execution_history_records_retry_lifecycle_across_attempts():
    from app.domain.execution import Execution
    from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository

    history = InMemoryExecutionHistoryRepository()
    executions = EventRecordingExecutionRepository(
        InMemoryExecutionRepository(),
        history,
    )
    execution = Execution.create(uuid4())

    execution.start()
    executions.save(execution)
    execution.fail()
    executions.save(execution)
    execution.retry()
    executions.save(execution)
    execution.start()
    executions.save(execution)
    execution.complete()
    executions.save(execution)

    entries = history.list(execution.id)

    assert [event.event_type for event in entries] == [
        "execution.started",
        "execution.failed",
        "execution.retrying",
        "execution.retry_started",
        "execution.completed",
    ]
    assert [event.attempt for event in entries] == [1, 1, 2, 2, 2]
    assert [event.sequence for event in entries] == [1, 2, 3, 4, 5]


def test_execution_history_records_cancellation_from_created_state():
    from app.domain.execution import Execution
    from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository

    history = InMemoryExecutionHistoryRepository()
    executions = EventRecordingExecutionRepository(
        InMemoryExecutionRepository(),
        history,
    )
    execution = Execution.create(uuid4())

    execution.cancel()
    executions.save(execution)

    entries = history.list(execution.id)

    assert len(entries) == 1
    assert entries[0].event_type == "execution.cancelled"
    assert entries[0].state is ExecutionState.CANCELLED
    assert entries[0].attempt == 1
    assert entries[0].sequence == 1


def test_execution_history_rejects_non_contiguous_sequence():
    from datetime import datetime
    from app.domain.execution_event import ExecutionEvent

    history = InMemoryExecutionHistoryRepository()
    execution_id = uuid4()
    workflow_id = uuid4()

    first = ExecutionEvent(
        execution_id=execution_id,
        workflow_id=workflow_id,
        sequence=1,
        event_type="execution.started",
        state=ExecutionState.RUNNING,
        attempt=1,
        occurred_at=datetime.now(),
    )
    skipped = ExecutionEvent(
        execution_id=execution_id,
        workflow_id=workflow_id,
        sequence=3,
        event_type="execution.completed",
        state=ExecutionState.COMPLETED,
        attempt=1,
        occurred_at=datetime.now(),
    )

    history.append(first)

    with pytest.raises(
        ValueError,
        match="Execution history sequence must be appended in order",
    ):
        history.append(skipped)

    assert history.list(execution_id) == (first,)


def test_execution_history_rejects_conflicting_event_at_existing_sequence():
    from datetime import datetime
    from app.domain.execution_event import ExecutionEvent

    history = InMemoryExecutionHistoryRepository()
    execution_id = uuid4()
    workflow_id = uuid4()

    first = ExecutionEvent(
        execution_id=execution_id,
        workflow_id=workflow_id,
        sequence=1,
        event_type="execution.started",
        state=ExecutionState.RUNNING,
        attempt=1,
        occurred_at=datetime.now(),
    )
    conflicting = ExecutionEvent(
        execution_id=execution_id,
        workflow_id=workflow_id,
        sequence=1,
        event_type="execution.failed",
        state=ExecutionState.FAILED,
        attempt=1,
        occurred_at=datetime.now(),
    )

    history.append(first)

    with pytest.raises(
        ValueError,
        match="sequence already contains a different event",
    ):
        history.append(conflicting)

    assert history.list(execution_id) == (first,)


def test_idempotency_record_pointing_to_missing_execution_is_rejected():
    from datetime import datetime, timezone

    from app.domain.repositories import ExecutionIdempotencyRecord
    from app.infrastructure.persistence.in_memory import (
        InMemoryExecutionRepository,
        InMemoryWorkflowRepository,
    )

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    idempotency = InMemoryExecutionIdempotencyRepository()
    workflow = published_workflow("Missing Execution")
    workflows.save(workflow)

    idempotency.reserve(
        ExecutionIdempotencyRecord(
            key="orphan-key",
            workflow_id=workflow.id,
            execution_id=uuid4(),
            created_at=datetime.now(timezone.utc),
        )
    )

    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
    )

    with pytest.raises(RuntimeError, match="Idempotency record points to missing execution"):
        start.execute(workflow.id, idempotency_key="orphan-key")


def test_idempotency_reservation_is_released_when_execution_save_fails():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    class FailingExecutionRepository:
        def save(self, execution):
            raise RuntimeError("execution persistence unavailable")

        def get(self, execution_id):
            return None

        def all(self):
            return ()

    workflows = InMemoryWorkflowRepository()
    workflow = published_workflow("Persistence Failure")
    workflows.save(workflow)
    idempotency = InMemoryExecutionIdempotencyRepository()

    start = StartWorkflowExecution(
        workflows,
        FailingExecutionRepository(),
        idempotency_repository=idempotency,
    )

    with pytest.raises(RuntimeError, match="execution persistence unavailable"):
        start.execute(workflow.id, idempotency_key="recoverable-key")

    assert idempotency.get("recoverable-key") is None
