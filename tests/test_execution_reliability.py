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
    InMemoryExecutionStartRepository,
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
        execution_start_repository=InMemoryExecutionStartRepository(
            executions, idempotency
        ),
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
        execution_start_repository=InMemoryExecutionStartRepository(executions, idempotency),
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

    idempotency = InMemoryExecutionIdempotencyRepository()
    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=InMemoryExecutionStartRepository(executions, idempotency),
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
        "orphan-key",
        workflow.id,
        uuid4(),
    )

    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=InMemoryExecutionStartRepository(executions, idempotency),
    )

    with pytest.raises(RuntimeError, match="Idempotency record references a missing execution"):
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
    executions = FailingExecutionRepository()
    workflow = published_workflow("Persistence Failure")
    workflows.save(workflow)
    idempotency = InMemoryExecutionIdempotencyRepository()

    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=InMemoryExecutionStartRepository(
            executions, idempotency
        ),
    )

    with pytest.raises(RuntimeError, match="execution persistence unavailable"):
        start.execute(workflow.id, idempotency_key="recoverable-key")

    assert idempotency.get("recoverable-key") is None


def test_idempotency_key_is_normalized_before_lookup_and_reservation():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow("Normalized Key")
    workflows.save(workflow)
    idempotency = InMemoryExecutionIdempotencyRepository()
    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=InMemoryExecutionStartRepository(executions, idempotency),
    )

    first = start.execute(workflow.id, idempotency_key="  normalized-key  ")
    second = start.execute(workflow.id, idempotency_key="normalized-key")

    assert second is first
    assert len(executions.all()) == 1
    assert idempotency.get("normalized-key") is not None
    assert idempotency.get("  normalized-key  ") is None


def test_duplicate_idempotent_start_replays_current_execution_state():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow("Replay Current State")
    workflows.save(workflow)
    idempotency = InMemoryExecutionIdempotencyRepository()
    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=InMemoryExecutionStartRepository(executions, idempotency),
    )

    first = start.execute(workflow.id, idempotency_key="replay-key")
    first.complete()

    second = start.execute(workflow.id, idempotency_key="replay-key")

    assert second is first
    assert second.state is ExecutionState.COMPLETED
    assert len(executions.all()) == 1


def test_idempotency_reserve_failure_does_not_persist_execution():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    class FailingIdempotencyRepository:
        def get(self, key):
            return None

        def reserve(self, key, workflow_id, execution_id):
            raise RuntimeError("idempotency persistence unavailable")

        def release(self, key, execution_id):
            raise AssertionError("release must not run when reserve fails")

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow("Reserve Failure")
    workflows.save(workflow)

    idempotency = FailingIdempotencyRepository()
    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=InMemoryExecutionStartRepository(
            executions, idempotency
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="idempotency persistence unavailable",
    ):
        start.execute(workflow.id, idempotency_key="reserve-failure-key")

    assert executions.all() == ()


def test_idempotency_lookup_failure_does_not_create_execution():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    class FailingLookupIdempotencyRepository:
        def get(self, key):
            raise RuntimeError("idempotency lookup unavailable")

        def reserve(self, key, workflow_id, execution_id):
            raise AssertionError("reserve must not run when lookup fails")

        def release(self, key, execution_id):
            raise AssertionError("release must not run when lookup fails")

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow("Lookup Failure")
    workflows.save(workflow)

    idempotency = FailingLookupIdempotencyRepository()
    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=InMemoryExecutionStartRepository(
            executions, idempotency
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="idempotency lookup unavailable",
    ):
        start.execute(workflow.id, idempotency_key="lookup-failure-key")

    assert executions.all() == ()


def test_idempotency_reservation_is_atomic_under_concurrent_claims():
    from concurrent.futures import ThreadPoolExecutor

    idempotency = InMemoryExecutionIdempotencyRepository()
    workflow_id = uuid4()

    def reserve(index):
        return idempotency.reserve(
            "concurrent-key",
            workflow_id,
            uuid4(),
        )

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(reserve, range(16)))

    created = [result for result in results if result[1]]
    existing = [result[0] for result in results]

    assert len(created) == 1
    assert all(record == created[0][0] for record in existing)


def test_duplicate_after_history_persistence_failure_replays_persisted_execution():
    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    class ToggleHistoryRepository:
        def __init__(self):
            self.fail = True
            self.events = []

        def append(self, event):
            if self.fail:
                raise RuntimeError("history temporarily unavailable")
            self.events.append(event)

        def list(self, execution_id):
            return tuple(
                event for event in self.events if event.execution_id == execution_id
            )

    workflows = InMemoryWorkflowRepository()
    inner_executions = InMemoryExecutionRepository()
    history = ToggleHistoryRepository()
    executions = EventRecordingExecutionRepository(inner_executions, history)
    idempotency = InMemoryExecutionIdempotencyRepository()
    workflow = published_workflow("Partial History Failure")
    workflows.save(workflow)

    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=InMemoryExecutionStartRepository(executions, idempotency),
    )

    with pytest.raises(
        RuntimeError,
        match="history temporarily unavailable",
    ):
        start.execute(workflow.id, idempotency_key="partial-failure-key")

    persisted = next(iter(inner_executions.all()))
    assert persisted.state is ExecutionState.RUNNING
    assert idempotency.get("partial-failure-key") is not None

    history.fail = False

    replayed = start.execute(
        workflow.id,
        idempotency_key="partial-failure-key",
    )

    assert replayed is persisted
    assert replayed.state is ExecutionState.RUNNING
    assert len(inner_executions.all()) == 1


def test_api_surfaces_idempotency_persistence_failure_as_server_error():
    import app.api.execution as execution_api

    class FailingStart:
        def execute(self, workflow_id, idempotency_key=None):
            raise RuntimeError("idempotency persistence unavailable")

    original = execution_api.start_workflow_execution
    execution_api.start_workflow_execution = FailingStart()
    isolated_client = TestClient(app, raise_server_exceptions=False)

    try:
        response = isolated_client.post(
            f"/executions/workflows/{uuid4()}",
            headers={"Idempotency-Key": "persistence-failure-key"},
        )
    finally:
        execution_api.start_workflow_execution = original

    assert response.status_code == 500



def test_concurrent_duplicate_start_resolves_to_the_persisted_execution():
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event

    from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository

    class BlockingExecutionRepository(InMemoryExecutionRepository):
        def __init__(self):
            super().__init__()
            self.block_save = Event()
            self.allow_save = Event()

        def save(self, execution):
            self.block_save.set()
            self.allow_save.wait(timeout=5)
            super().save(execution)

    workflows = InMemoryWorkflowRepository()
    executions = BlockingExecutionRepository()
    workflow = published_workflow("Concurrent Duplicate Start")
    workflows.save(workflow)
    idempotency = InMemoryExecutionIdempotencyRepository()
    atomic_start = InMemoryExecutionStartRepository(executions, idempotency)
    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=atomic_start,
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(
            start.execute,
            workflow.id,
            "concurrent-start-key",
        )
        assert executions.block_save.wait(timeout=5)

        duplicate_future = pool.submit(
            start.execute,
            workflow.id,
            "concurrent-start-key",
        )

        with pytest.raises(TimeoutError):
            duplicate_future.result(timeout=0.2)

        executions.allow_save.set()
        first_result = first_future.result(timeout=5)
        duplicate_result = duplicate_future.result(timeout=5)

    assert duplicate_result.id == first_result.id
    assert len(executions.all()) == 1
