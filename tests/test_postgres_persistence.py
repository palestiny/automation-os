from __future__ import annotations

import os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from app.application.execution_metrics import GetExecutionMetrics
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.connection import Connection, ConnectionRequirement, ConnectionStatus
from app.domain.execution import Execution, ExecutionState
from app.domain.execution_event import ExecutionEvent
from app.domain.marketplace import MarketplaceListing
from app.domain.repositories import ExecutionIdempotencyRepository
from app.domain.review_decision import ReviewDecision, ReviewDecisionType
from app.domain.workflow import Workflow, WorkflowState, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.migrations import PostgresMigrationRunner
from app.infrastructure.persistence.postgres import (
    PostgresConnectionRepository,
    PostgresExecutionHistoryRepository,
    PostgresExecutionIdempotencyRepository,
    PostgresExecutionRepository,
    PostgresExecutionStartRepository,
    PostgresMarketplaceListingRepository,
    PostgresMarketplaceRepository,
    PostgresWorkflowRepository,
    PostgresWorkflowVersionRepository,
    PostgresReviewDecisionRepository,
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
        PostgresMigrationRunner(factory).apply()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE
                    connections,
                    review_decisions,
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


def test_review_decision_survives_recreation_and_replays_idempotently(connection_factory):
    tenant_id = uuid4()
    decision = ReviewDecision.create(
        workflow_id=uuid4(),
        workflow_revision="a" * 64,
        tenant_id=tenant_id,
        reviewer_principal_id="reviewer-1",
        decision=ReviewDecisionType.APPROVED,
        reason="Validated",
        idempotency_key="review-key",
        created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    repository = PostgresReviewDecisionRepository(connection_factory, tenant_id=tenant_id)
    first, created = repository.save_idempotent(decision)
    second, replayed = PostgresReviewDecisionRepository(
        connection_factory, tenant_id=tenant_id
    ).save_idempotent(decision)

    assert created is True
    assert replayed is False
    assert first == decision
    assert second == decision
    assert PostgresReviewDecisionRepository(connection_factory, tenant_id=tenant_id).get_by_idempotency_key("review-key") == decision


def test_review_decision_rejects_cross_tenant_write(connection_factory):
    decision = ReviewDecision.create(
        workflow_id=uuid4(),
        workflow_revision="b" * 64,
        tenant_id=uuid4(),
        reviewer_principal_id="reviewer-1",
        decision=ReviewDecisionType.APPROVED,
        reason=None,
        idempotency_key="review-key",
    )
    repository = PostgresReviewDecisionRepository(connection_factory, tenant_id=uuid4())

    with pytest.raises(ValueError, match="different tenant"):
        repository.save_idempotent(decision)


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
    workflow = Workflow.create(
        name="durable workflow",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        supported_goals=["durable-test"],
        required_parameters=["name"],
        tenant_id=tenant_a,
    )
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


def test_human_review_application_persists_and_replays_after_repository_recreation(connection_factory):
    from app.application.authorization import AuthorizationContext, TenantId
    from app.application.review_workflow import ApproveWorkflow

    tenant_id = uuid4()
    workflow = Workflow.create(
        name="reviewable workflow",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        supported_goals=["review-test"],
        tenant_id=tenant_id,
    )
    workflow_repository = PostgresWorkflowRepository(
        connection_factory, tenant_id=tenant_id
    )
    review_repository = PostgresReviewDecisionRepository(
        connection_factory, tenant_id=tenant_id
    )
    workflow_repository.save(workflow)
    context = AuthorizationContext(
        principal_id="reviewer-1",
        tenant_id=TenantId(tenant_id),
    )

    first = ApproveWorkflow(
        workflow_repository,
        review_repository,
        clock=lambda: datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
    ).execute(
        workflow.id,
        context,
        idempotency_key="human-review-1",
        expected_revision=workflow.review_revision,
    )

    recreated_workflow_repository = PostgresWorkflowRepository(
        connection_factory, tenant_id=tenant_id
    )
    recreated_review_repository = PostgresReviewDecisionRepository(
        connection_factory, tenant_id=tenant_id
    )
    replay = ApproveWorkflow(
        recreated_workflow_repository,
        recreated_review_repository,
    ).execute(
        workflow.id,
        context,
        idempotency_key="human-review-1",
        expected_revision=workflow.review_revision,
    )

    assert replay == first
    assert recreated_review_repository.list_by_workflow(workflow.id) == (first,)
    assert recreated_workflow_repository.get(workflow.id).state.value == "draft"


def test_human_review_same_idempotency_key_is_isolated_between_tenants(connection_factory):
    from app.application.authorization import AuthorizationContext, TenantId
    from app.application.review_workflow import ApproveWorkflow

    tenant_a = uuid4()
    tenant_b = uuid4()
    workflow_a = Workflow.create(
        name="tenant a workflow",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        supported_goals=["review-test"],
        tenant_id=tenant_a,
    )
    workflow_b = Workflow.create(
        name="tenant b workflow",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        supported_goals=["review-test"],
        tenant_id=tenant_b,
    )

    repo_a = PostgresWorkflowRepository(connection_factory, tenant_id=tenant_a)
    repo_b = PostgresWorkflowRepository(connection_factory, tenant_id=tenant_b)
    decisions_a = PostgresReviewDecisionRepository(connection_factory, tenant_id=tenant_a)
    decisions_b = PostgresReviewDecisionRepository(connection_factory, tenant_id=tenant_b)
    repo_a.save(workflow_a)
    repo_b.save(workflow_b)

    first = ApproveWorkflow(repo_a, decisions_a).execute(
        workflow_a.id,
        AuthorizationContext(
            principal_id="reviewer-a",
            tenant_id=TenantId(tenant_a),
        ),
        idempotency_key="shared-review-key",
        expected_revision=workflow_a.review_revision,
    )
    second = ApproveWorkflow(repo_b, decisions_b).execute(
        workflow_b.id,
        AuthorizationContext(
            principal_id="reviewer-b",
            tenant_id=TenantId(tenant_b),
        ),
        idempotency_key="shared-review-key",
        expected_revision=workflow_b.review_revision,
    )

    assert first.id != second.id
    assert decisions_a.get_by_idempotency_key("shared-review-key") == first
    assert decisions_b.get_by_idempotency_key("shared-review-key") == second


def test_human_review_conflicting_replay_is_rejected_durably(connection_factory):
    from app.application.authorization import AuthorizationContext, TenantId
    from app.application.review_workflow import ApproveWorkflow, RejectWorkflow

    tenant_id = uuid4()
    workflow = Workflow.create(
        name="conflict workflow",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        supported_goals=["review-test"],
        tenant_id=tenant_id,
    )
    workflow_repository = PostgresWorkflowRepository(
        connection_factory, tenant_id=tenant_id
    )
    review_repository = PostgresReviewDecisionRepository(
        connection_factory, tenant_id=tenant_id
    )
    workflow_repository.save(workflow)
    context = AuthorizationContext(
        principal_id="reviewer-1",
        tenant_id=TenantId(tenant_id),
    )

    ApproveWorkflow(workflow_repository, review_repository).execute(
        workflow.id,
        context,
        idempotency_key="conflict-key",
        expected_revision=workflow.review_revision,
    )

    recreated_review_repository = PostgresReviewDecisionRepository(
        connection_factory, tenant_id=tenant_id
    )
    with pytest.raises(ValueError, match="conflicts"):
        RejectWorkflow(
            PostgresWorkflowRepository(connection_factory, tenant_id=tenant_id),
            recreated_review_repository,
        ).execute(
            workflow.id,
            context,
            idempotency_key="conflict-key",
            expected_revision=workflow.review_revision,
            reason="Invalid output",
        )

    assert len(recreated_review_repository.list_by_workflow(workflow.id)) == 1


def test_human_review_stale_revision_is_rejected_against_durable_workflow(connection_factory):
    from app.application.authorization import AuthorizationContext, TenantId
    from app.application.review_workflow import ApproveWorkflow, StaleWorkflowReviewError

    tenant_id = uuid4()
    workflow = Workflow.create(
        name="stale review workflow",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        supported_goals=["review-test"],
        tenant_id=tenant_id,
    )
    repository = PostgresWorkflowRepository(connection_factory, tenant_id=tenant_id)
    review_repository = PostgresReviewDecisionRepository(
        connection_factory, tenant_id=tenant_id
    )
    repository.save(workflow)
    reviewed_revision = workflow.review_revision

    workflow.add_step(
        WorkflowStep.create(name="second step", capability="test.capability")
    )
    repository.save(workflow)

    with pytest.raises(StaleWorkflowReviewError):
        ApproveWorkflow(repository, review_repository).execute(
            workflow.id,
            AuthorizationContext(
                principal_id="reviewer-1",
                tenant_id=TenantId(tenant_id),
            ),
            idempotency_key="stale-review-key",
            expected_revision=reviewed_revision,
        )

    assert review_repository.list_by_workflow(workflow.id) == ()
    assert repository.get(workflow.id).state.value == "draft"


def test_system_review_decisions_are_null_tenant_and_hidden_from_tenant_repositories(
    connection_factory,
):
    from app.application.authorization import AuthorizationContext
    from app.application.review_workflow import ApproveWorkflow

    workflow = Workflow.create(
        name="system review workflow",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
        supported_goals=["review-test"],
        tenant_id=None,
    )
    workflow_repository = PostgresWorkflowRepository(connection_factory)
    review_repository = PostgresReviewDecisionRepository(connection_factory)
    workflow_repository.save(workflow)

    decision = ApproveWorkflow(workflow_repository, review_repository).execute(
        workflow.id,
        AuthorizationContext.system("system-reviewer"),
        idempotency_key="system-review-key",
        expected_revision=workflow.review_revision,
    )

    assert decision.tenant_id is None
    assert review_repository.get_by_idempotency_key("system-review-key") == decision
    assert review_repository.list_by_workflow(workflow.id) == (decision,)

    tenant_review_repository = PostgresReviewDecisionRepository(
        connection_factory, tenant_id=uuid4()
    )
    assert tenant_review_repository.get_by_idempotency_key("system-review-key") is None
    assert tenant_review_repository.list_by_workflow(workflow.id) == ()



def _connection(tenant_id):
    return Connection.create(
        tenant_id=tenant_id,
        provider_id="youtube",
        reference="youtube.primary",
        authentication_type="api_key",
        secret_reference="secret://youtube/primary",
        clock=lambda: datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


def test_connection_survives_postgres_repository_recreation_without_secret_material(connection_factory):
    tenant_id = uuid4()
    connection = _connection(tenant_id)
    repository = PostgresConnectionRepository(connection_factory, tenant_id=tenant_id)
    repository.save(connection)

    recreated = PostgresConnectionRepository(connection_factory, tenant_id=tenant_id)
    assert recreated.get(connection.id) == connection
    assert recreated.get_by_reference("youtube.primary", "youtube") == connection
    assert recreated.all() == (connection,)

    with connection_factory() as database:
        with database.cursor() as cursor:
            cursor.execute(
                "SELECT provider_id, reference, authentication_type, secret_reference, status FROM connections WHERE id = %s",
                (connection.id,),
            )
            row = cursor.fetchone()
    assert row == ("youtube", "youtube.primary", "api_key", "secret://youtube/primary", "active")


def test_connections_are_tenant_scoped_and_same_reference_can_exist_in_other_tenant(connection_factory):
    tenant_a = uuid4()
    tenant_b = uuid4()
    first = _connection(tenant_a)
    second = Connection.create(
        tenant_id=tenant_b,
        provider_id=first.provider_id,
        reference=first.reference,
        authentication_type=first.authentication_type,
        secret_reference="secret://youtube/tenant-b",
    )

    PostgresConnectionRepository(connection_factory, tenant_id=tenant_a).save(first)
    PostgresConnectionRepository(connection_factory, tenant_id=tenant_b).save(second)

    assert PostgresConnectionRepository(connection_factory, tenant_id=tenant_a).get(first.id) == first
    assert PostgresConnectionRepository(connection_factory, tenant_id=tenant_a).get(second.id) is None
    assert PostgresConnectionRepository(connection_factory, tenant_id=tenant_b).get(first.id) is None


def test_connection_duplicate_provider_reference_is_rejected_by_durable_constraint(connection_factory):
    tenant_id = uuid4()
    first = _connection(tenant_id)
    duplicate = Connection.create(
        tenant_id=tenant_id,
        provider_id=first.provider_id,
        reference=first.reference,
        authentication_type="oauth",
        secret_reference="secret://youtube/duplicate",
    )
    repository = PostgresConnectionRepository(connection_factory, tenant_id=tenant_id)
    repository.save(first)

    with pytest.raises(Exception):
        repository.save(duplicate)


def test_revoked_connection_round_trips_as_revoked(connection_factory):
    tenant_id = uuid4()
    connection = _connection(tenant_id)
    connection.revoke(clock=lambda: datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc))
    repository = PostgresConnectionRepository(connection_factory, tenant_id=tenant_id)
    repository.save(connection)

    loaded = PostgresConnectionRepository(connection_factory, tenant_id=tenant_id).get(connection.id)
    assert loaded == connection
    assert loaded.status is ConnectionStatus.REVOKED


def test_connection_rejects_cross_tenant_write(connection_factory):
    connection = _connection(uuid4())
    repository = PostgresConnectionRepository(connection_factory, tenant_id=uuid4())

    with pytest.raises(ValueError, match="different tenant"):
        repository.save(connection)



def test_workflow_version_connection_requirements_round_trip_durably(connection_factory):
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="connection-aware workflow",
        steps=[WorkflowStep.create(name="publish", capability="youtube.publish")],
        tenant_id=tenant_id,
    )
    requirement = ConnectionRequirement.create("youtube", "youtube.primary")
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_id,
        connection_requirements=[requirement],
    )
    version.publish()

    repository = PostgresWorkflowVersionRepository(
        connection_factory, tenant_id=tenant_id
    )
    repository.save(version)

    recreated = PostgresWorkflowVersionRepository(
        connection_factory, tenant_id=tenant_id
    ).get(version.id)

    assert recreated is not None
    assert recreated.connection_requirements == (requirement,)
    assert recreated.state is WorkflowState.PUBLISHED

    with connection_factory() as database:
        with database.cursor() as cursor:
            cursor.execute(
                "SELECT payload FROM workflow_versions WHERE id = %s",
                (version.id,),
            )
            payload = cursor.fetchone()[0]

    assert payload["connection_requirements"] == [
        {"provider_id": "youtube", "reference": "youtube.primary"}
    ]
    assert "secret_reference" not in payload["connection_requirements"][0]
def test_execution_persists_external_outcome_retry_safety_evidence(connection_factory):
    from app.infrastructure.persistence.postgres import PostgresExecutionRepository

    execution = Execution.create(uuid4())
    execution.start()
    execution.fail(
        outcome="unknown",
        operation_id="operation-123",
        diagnostic="provider accepted request before connection loss",
        idempotency_proven=False,
        retryable=False,
    )

    repository = PostgresExecutionRepository(connection_factory)
    repository.save(execution)

    recreated = repository.get(execution.id)

    assert recreated is not None
    assert recreated.last_outcome == "unknown"
    assert recreated.last_operation_id == "operation-123"
    assert recreated.last_idempotency_proven is False
    assert recreated.last_retryable is False

