from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.execution import Execution
from app.domain.repositories import ExecutionIdempotencyRepository
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.postgres import (
    PostgresExecutionHistoryRepository,
    PostgresExecutionIdempotencyRepository,
    PostgresExecutionRepository,
    PostgresExecutionStartRepository,
    PostgresSchema,
    PostgresWorkflowRepository,
    postgres_connection_factory,
)


DATABASE_URL = os.environ.get("AUTOMATION_OS_TEST_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="AUTOMATION_OS_TEST_DATABASE_URL is required for PostgreSQL persistence tests",
)


@pytest.fixture()
def connection_factory():
    factory = postgres_connection_factory(DATABASE_URL)
    with factory() as connection:
        PostgresSchema.initialize(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE
                    execution_history,
                    execution_idempotency,
                    executions,
                    workflows
                """
            )
        connection.commit()
    return factory


def _workflow() -> Workflow:
    return Workflow.create(
        name="durable workflow",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        supported_goals=["durable-test"],
        required_parameters=["name"],
    )


def _repositories(connection_factory):
    workflow_repository = PostgresWorkflowRepository(connection_factory)
    execution_repository = PostgresExecutionRepository(connection_factory)
    idempotency_repository = PostgresExecutionIdempotencyRepository(connection_factory)
    start_repository = PostgresExecutionStartRepository(connection_factory)
    history_repository = PostgresExecutionHistoryRepository(connection_factory)
    return (
        workflow_repository,
        execution_repository,
        idempotency_repository,
        start_repository,
        history_repository,
    )


def test_workflow_and_execution_survive_repository_recreation(connection_factory):
    workflow_repository, execution_repository, *_ = _repositories(connection_factory)
    workflow = _workflow()
    workflow.publish()
    workflow_repository.save(workflow)

    execution = Execution.create(workflow.id)
    execution.start()
    execution_repository.save(execution)

    workflow_repository_recreated = PostgresWorkflowRepository(connection_factory)
    execution_repository_recreated = PostgresExecutionRepository(connection_factory)

    loaded_workflow = workflow_repository_recreated.get(workflow.id)
    loaded_execution = execution_repository_recreated.get(execution.id)

    assert loaded_workflow == workflow
    assert loaded_execution == execution


def test_idempotency_survives_repository_recreation(connection_factory):
    workflow_repository, execution_repository, idempotency_repository, start_repository, _ = _repositories(
        connection_factory
    )
    workflow = _workflow()
    workflow.publish()
    workflow_repository.save(workflow)

    service = StartWorkflowExecution(
        workflow_repository,
        execution_repository,
        idempotency_repository=idempotency_repository,
        execution_start_repository=start_repository,
    )
    first = service.execute(workflow.id, idempotency_key="durable-key")

    recreated_service = StartWorkflowExecution(
        PostgresWorkflowRepository(connection_factory),
        PostgresExecutionRepository(connection_factory),
        idempotency_repository=PostgresExecutionIdempotencyRepository(connection_factory),
        execution_start_repository=PostgresExecutionStartRepository(connection_factory),
    )
    second = recreated_service.execute(workflow.id, idempotency_key="durable-key")

    assert second.id == first.id
    assert second.attempt == 1


def test_concurrent_same_key_creates_one_execution(connection_factory):
    workflow_repository = PostgresWorkflowRepository(connection_factory)
    workflow = _workflow()
    workflow.publish()
    workflow_repository.save(workflow)

    def start():
        service = StartWorkflowExecution(
            PostgresWorkflowRepository(connection_factory),
            PostgresExecutionRepository(connection_factory),
            idempotency_repository=PostgresExecutionIdempotencyRepository(connection_factory),
            execution_start_repository=PostgresExecutionStartRepository(connection_factory),
        )
        return service.execute(workflow.id, idempotency_key="concurrent-key")

    with ThreadPoolExecutor(max_workers=8) as pool:
        executions = list(pool.map(lambda _: start(), range(8)))

    assert len({execution.id for execution in executions}) == 1
    assert len(PostgresExecutionRepository(connection_factory).all()) == 1


def test_same_key_for_different_workflow_is_rejected(connection_factory):
    workflow_repository = PostgresWorkflowRepository(connection_factory)
    first_workflow = _workflow()
    second_workflow = _workflow()
    first_workflow.publish()
    second_workflow.publish()
    workflow_repository.save(first_workflow)
    workflow_repository.save(second_workflow)

    service = StartWorkflowExecution(
        workflow_repository,
        PostgresExecutionRepository(connection_factory),
        idempotency_repository=PostgresExecutionIdempotencyRepository(connection_factory),
        execution_start_repository=PostgresExecutionStartRepository(connection_factory),
    )
    service.execute(first_workflow.id, idempotency_key="shared-key")

    with pytest.raises(ValueError, match="different workflow"):
        service.execute(second_workflow.id, idempotency_key="shared-key")


def test_history_is_append_only_and_ordered(connection_factory):
    _, execution_repository, _, _, history_repository = _repositories(connection_factory)
    workflow = _workflow()
    execution = Execution.create(workflow.id)
    execution.start()
    execution.complete()

    execution_repository.save(execution)
    execution_repository.save(execution)

    events = history_repository.list(execution.id)
    assert [event.sequence for event in events] == [1, 2]
    assert [event.event_type for event in events] == [
        "execution.started",
        "execution.completed",
    ]


def test_failed_atomic_start_does_not_leave_idempotency_record(connection_factory, monkeypatch):
    import app.infrastructure.persistence.postgres as postgres

    workflow = _workflow()
    execution = Execution.create(workflow.id)
    execution.start()
    repository = PostgresExecutionStartRepository(connection_factory)
    key = "rollback-key"

    def fail(*_args, **_kwargs):
        raise RuntimeError("forced persistence failure")

    monkeypatch.setattr(postgres, "_upsert_execution", fail)

    with pytest.raises(RuntimeError, match="forced persistence failure"):
        repository.save_idempotent(execution, key)

    idempotency = PostgresExecutionIdempotencyRepository(connection_factory)
    assert idempotency.get(key) is None


def test_domain_and_application_contracts_remain_repository_based(connection_factory):
    workflow_repository, execution_repository, idempotency_repository, start_repository, _ = _repositories(
        connection_factory
    )
    assert isinstance(workflow_repository, PostgresWorkflowRepository)
    assert isinstance(execution_repository, PostgresExecutionRepository)
    assert isinstance(idempotency_repository, ExecutionIdempotencyRepository)
    assert isinstance(start_repository, PostgresExecutionStartRepository)
