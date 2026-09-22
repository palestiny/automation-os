from __future__ import annotations

import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from app.application.execution_metrics import GetExecutionMetrics
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.execution import Execution, ExecutionState
from app.domain.execution_event import ExecutionEvent
from app.domain.marketplace import MarketplaceListing
from app.domain.repositories import ExecutionIdempotencyRepository
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.postgres import (
    PostgresExecutionHistoryRepository,
    PostgresExecutionIdempotencyRepository,
    PostgresExecutionRepository,
    PostgresExecutionStartRepository,
    PostgresMarketplaceListingRepository,
    PostgresMarketplaceRepository,
    PostgresSchema,
    PostgresWorkflowRepository,
    PostgresWorkflowVersionRepository,
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
                    workflow_versions,
                    marketplace_listings,
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
    workflow_version_repository = PostgresWorkflowVersionRepository(connection_factory)
    execution_repository = PostgresExecutionRepository(connection_factory)
    idempotency_repository = PostgresExecutionIdempotencyRepository(connection_factory)
    start_repository = PostgresExecutionStartRepository(connection_factory)
    history_repository = PostgresExecutionHistoryRepository(connection_factory)
    return (
        workflow_repository,
        workflow_version_repository,
        execution_repository,
        idempotency_repository,
        start_repository,
        history_repository,
    )


def test_workflow_and_execution_survive_repository_recreation(connection_factory):
    workflow_repository, workflow_version_repository, execution_repository, *_ = _repositories(connection_factory)
    workflow = _workflow()
    workflow.publish()
    workflow_repository.save(workflow)

    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    workflow_version_repository.save(version)
    execution = Execution.create(workflow.id, workflow_version_id=version.id)
    execution.start()
    execution_repository.save(execution)

    workflow_repository_recreated = PostgresWorkflowRepository(connection_factory)
    execution_repository_recreated = PostgresExecutionRepository(connection_factory)

    loaded_workflow = workflow_repository_recreated.get(workflow.id)
    loaded_execution = execution_repository_recreated.get(execution.id)

    assert loaded_workflow == workflow
    assert loaded_execution == execution


def test_idempotency_survives_repository_recreation(connection_factory):
    workflow_repository, _, execution_repository, idempotency_repository, start_repository, _ = _repositories(
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
    _, _, execution_repository, _, _, history_repository = _repositories(connection_factory)
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


def test_execution_save_rolls_back_when_event_persistence_fails(connection_factory, monkeypatch):
    import app.infrastructure.persistence.postgres as postgres

    repository = PostgresExecutionRepository(connection_factory)
    workflow_id = uuid4()
    execution = Execution.create(workflow_id)
    execution.start()

    original_insert = postgres._insert_event
    calls = 0

    def fail_on_event(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("forced event persistence failure")
        return original_insert(*args, **kwargs)

    monkeypatch.setattr(postgres, "_insert_event", fail_on_event)

    with pytest.raises(RuntimeError, match="forced event persistence failure"):
        repository.save(execution)

    assert repository.get(execution.id) is None
    with connection_factory() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM execution_history WHERE execution_id = %s", (execution.id,))
            assert cursor.fetchone()[0] == 0


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


def test_execution_history_rejects_sequence_gap(connection_factory):
    repository = PostgresExecutionHistoryRepository(connection_factory)
    execution_id = uuid4()
    workflow_id = uuid4()
    event = ExecutionEvent(
        execution_id=execution_id,
        workflow_id=workflow_id,
        sequence=2,
        event_type="execution.completed",
        state=ExecutionState.COMPLETED,
        attempt=1,
        occurred_at=datetime(2026, 1, 1, 12, 0, 0),
    )

    with pytest.raises(ValueError, match="must be appended in order"):
        repository.append(event)


def test_domain_and_application_contracts_remain_repository_based(connection_factory):
    workflow_repository, _, execution_repository, idempotency_repository, start_repository, _ = _repositories(
        connection_factory
    )
    assert isinstance(workflow_repository, PostgresWorkflowRepository)
    assert isinstance(execution_repository, PostgresExecutionRepository)
    assert isinstance(idempotency_repository, ExecutionIdempotencyRepository)
    assert isinstance(start_repository, PostgresExecutionStartRepository)

def test_conditional_execution_recovery_cannot_overwrite_newer_state(connection_factory):
    repository = PostgresExecutionRepository(connection_factory)
    execution = Execution(
        id=uuid4(),
        workflow_id=uuid4(),
        current_step=0,
        state=ExecutionState.RUNNING,
        attempt=1,
        started_at=datetime(2026, 1, 1, 11, 0, 0),
    )
    repository.save(execution)

    first = repository.get(execution.id)
    second = repository.get(execution.id)
    first.recover_stale()

    assert repository.save_if_state(first, ExecutionState.RUNNING) is True

    second.recover_stale()

    assert repository.save_if_state(second, ExecutionState.RUNNING) is False
    assert repository.get(execution.id).state is ExecutionState.FAILED


def test_postgres_recovery_transition_persists_recovery_evidence(connection_factory):
    repository = PostgresExecutionRepository(connection_factory)
    history = PostgresExecutionHistoryRepository(connection_factory)
    execution = Execution(
        id=uuid4(),
        workflow_id=uuid4(),
        current_step=0,
        state=ExecutionState.RUNNING,
        attempt=1,
        started_at=datetime(2026, 1, 1, 11, 0, 0),
    )
    repository.save(execution)

    recovered = repository.get(execution.id)
    recovered.recover_stale()
    assert repository.save_if_state(recovered, ExecutionState.RUNNING) is True

    events = history.list(execution.id)
    assert events[-1].event_type == "execution.recovered_stale"
    assert repository.get(execution.id).state is ExecutionState.FAILED



def test_workflow_version_and_execution_version_survive_repository_recreation(connection_factory):
    workflow_repository = PostgresWorkflowRepository(connection_factory)
    version_repository = PostgresWorkflowVersionRepository(connection_factory)
    execution_repository = PostgresExecutionRepository(connection_factory)
    workflow = _workflow()
    workflow.publish()
    workflow_repository.save(workflow)

    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    version_repository.save(version)

    execution = Execution.create(workflow.id, workflow_version_id=version.id)
    execution.start()
    execution_repository.save(execution)

    loaded_version = PostgresWorkflowVersionRepository(connection_factory).get(version.id)
    loaded_execution = PostgresExecutionRepository(connection_factory).get(execution.id)

    assert loaded_version == version
    assert loaded_execution.workflow_version_id == version.id


def test_execution_metrics_match_persisted_postgres_evidence(connection_factory):
    _, version_repository, execution_repository, _, _, history_repository = _repositories(
        connection_factory
    )
    workflow = _workflow()
    workflow.publish()

    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    version_repository.save(version)

    execution = Execution.create(workflow.id, workflow_version_id=version.id)
    execution.start()
    execution.complete()
    execution_repository.save(execution)

    metrics = GetExecutionMetrics(
        execution_repository,
        history_repository,
    ).execute(
        datetime(2026, 1, 1, 0, 0, 0),
        datetime(2027, 1, 1, 0, 0, 0),
    )

    assert metrics.total_executions == 1
    assert metrics.state_counts["completed"] == 1
    assert metrics.workflow_breakdown == {str(workflow.id): 1}
    assert metrics.workflow_version_breakdown == {str(version.id): 1}
    assert metrics.retry_count == 0
    assert metrics.recovery_count == 0
    assert metrics.completed_duration_seconds is not None




def test_marketplace_listing_survives_postgres_repository_recreation(connection_factory):
    from app.infrastructure.persistence.postgres import PostgresMarketplaceListingRepository
    from app.domain.marketplace import MarketplaceListing

    repository = PostgresMarketplaceListingRepository(connection_factory)
    listing = MarketplaceListing.create(
        workflow_id=uuid4(),
        workflow_version_id=uuid4(),
        title="Marketplace listing",
        description="Durable listing",
        domain="automation",
        supported_goals=("test_goal",),
        tags=("test",),
    ).publish()

    repository.save(listing)

    recreated = PostgresMarketplaceListingRepository(connection_factory)

    assert recreated.get(listing.id) == listing
    assert recreated.all() == (listing,)



def test_tenant_scoped_workflow_and_execution_repositories_isolate_data(connection_factory):
    tenant_a = uuid4()
    tenant_b = uuid4()
    workflow = _workflow()
    workflow.publish()


def test_postgres_workflow_versions_are_tenant_scoped(connection_factory):
    tenant_a = uuid4()
    tenant_b = uuid4()
    workflow = _workflow()
    workflow.publish()
    PostgresWorkflowRepository(connection_factory, tenant_id=tenant_a).save(workflow)

    version = WorkflowVersion.create_from_workflow(workflow, 1, tenant_id=tenant_a)
    version.publish()
    PostgresWorkflowVersionRepository(connection_factory, tenant_id=tenant_a).save(version)

    tenant_a_repository = PostgresWorkflowVersionRepository(
        connection_factory, tenant_id=tenant_a
    )
    tenant_b_repository = PostgresWorkflowVersionRepository(
        connection_factory, tenant_id=tenant_b
    )

    assert tenant_a_repository.get(version.id) == version
    assert tenant_b_repository.get(version.id) is None
    assert tenant_b_repository.all() == ()


def test_postgres_workflow_version_rejects_cross_tenant_write(connection_factory):
    version = WorkflowVersion.create_from_workflow(
        _workflow(), 1, tenant_id=uuid4()
    )
    version.publish()
    repository = PostgresWorkflowVersionRepository(connection_factory, tenant_id=uuid4())

    with pytest.raises(ValueError, match="different tenant"):
        repository.save(version)


def test_postgres_marketplace_listings_are_tenant_scoped(connection_factory):
    tenant_a = uuid4()
    tenant_b = uuid4()
    listing = MarketplaceListing.create(
        workflow_id=uuid4(),
        workflow_version_id=uuid4(),
        title="Tenant listing",
        description="Tenant owned listing",
        domain="automation",
        supported_goals=("test_goal",),
        tags=("test",),
        tenant_id=tenant_a,
    ).publish()

    PostgresMarketplaceListingRepository(
        connection_factory, tenant_id=tenant_a
    ).save(listing)

    tenant_a_repository = PostgresMarketplaceListingRepository(
        connection_factory, tenant_id=tenant_a
    )
    tenant_b_repository = PostgresMarketplaceListingRepository(
        connection_factory, tenant_id=tenant_b
    )

    assert tenant_a_repository.get(listing.id) == listing
    assert tenant_b_repository.get(listing.id) is None
    assert tenant_b_repository.all() == ()


def test_postgres_marketplace_listing_rejects_cross_tenant_write(connection_factory):
    listing = MarketplaceListing.create(
        workflow_id=uuid4(),
        workflow_version_id=uuid4(),
        title="Tenant listing",
        description="Tenant owned listing",
        domain="automation",
        supported_goals=("test_goal",),
        tags=("test",),
        tenant_id=uuid4(),
    )
    repository = PostgresMarketplaceListingRepository(
        connection_factory, tenant_id=uuid4()
    )

    with pytest.raises(ValueError, match="different tenant"):
        repository.save(listing)

def test_postgres_null_tenant_rows_remain_system_scoped(connection_factory):
    workflow = _workflow()
    workflow.publish()
    workflow_repository = PostgresWorkflowRepository(connection_factory)
    workflow_repository.save(workflow)

    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    PostgresWorkflowVersionRepository(connection_factory).save(version)

    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="System listing",
        description="Legacy-compatible listing",
        domain="automation",
        supported_goals=("test_goal",),
        tags=("test",),
        tenant_id=None,
    ).publish()
    PostgresMarketplaceListingRepository(connection_factory).save(listing)

    tenant_repository = PostgresWorkflowVersionRepository(
        connection_factory, tenant_id=uuid4()
    )
    tenant_listing_repository = PostgresMarketplaceListingRepository(
        connection_factory, tenant_id=uuid4()
    )

    assert PostgresWorkflowVersionRepository(connection_factory).get(version.id) == version
    assert tenant_repository.get(version.id) is None
    assert PostgresMarketplaceListingRepository(connection_factory).get(listing.id) == listing
    assert tenant_listing_repository.get(listing.id) is None
