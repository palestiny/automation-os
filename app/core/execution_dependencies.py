from __future__ import annotations

import os

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionUseCases:
    """Execution application services composed for one authorization scope."""

    start_workflow_execution: StartWorkflowExecution
    execution_progress: GetExecutionProgress
    discover_executions: DiscoverExecutions
    cancel_execution: CancelExecution
    resume_execution: ResumeExecution
    retry_execution: RetryExecution
    retry_and_execute_execution: RetryAndExecuteExecution



from app.application.authorization import AuthorizationContext, AuthorizationPolicy
from app.application.cancel_execution import CancelExecution
from app.application.connection_resolver import ConnectionResolver
from app.application.connection_runtime_resolution import ResolveRuntimeConnection
from app.application.runtime_connection_preparation import PrepareWorkflowRuntimeConnections
from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_provider_resolver import CapabilityProviderResolver
from app.application.capability_registry import CapabilityRegistry
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.execution_discovery import DiscoverExecutions
from app.application.execution_progress import GetExecutionProgress
from app.application.resume_execution import ResumeExecution
from app.application.retry_and_execute_execution import RetryAndExecuteExecution
from app.application.retry_execution import RetryExecution
from app.application.start_retrying_execution import StartRetryingExecution
from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.core.job_manager import JobManager
from app.infrastructure.persistence.in_memory import (
    EventRecordingExecutionRepository,
    InMemoryExecutionHistoryRepository,
    InMemoryExecutionIdempotencyRepository,
    InMemoryExecutionRepository,
    InMemoryExecutionStartRepository,
    InMemoryWorkflowRepository,
    InMemoryWorkflowVersionRepository,
    InMemoryReviewDecisionRepository,
)
from app.infrastructure.secrets import UnconfiguredSecretProvider
from app.infrastructure.persistence.postgres import (
    PostgresExecutionHistoryRepository,
    PostgresExecutionIdempotencyRepository,
    PostgresExecutionRepository,
    PostgresExecutionStartRepository,
    PostgresSchema,
    PostgresWorkflowRepository,
    PostgresWorkflowVersionRepository,
    PostgresConnectionRepository,
    PostgresReviewDecisionRepository,
    postgres_connection_factory,
)

job_manager = JobManager()


def _build_persistence(tenant_id=None):
    database_url = os.environ.get("AUTOMATION_OS_DATABASE_URL")
    if not database_url:
        execution_store = InMemoryExecutionRepository()
        execution_history_repository = InMemoryExecutionHistoryRepository()
        execution_repository = EventRecordingExecutionRepository(
            execution_store,
            execution_history_repository,
        )
        execution_idempotency_repository = InMemoryExecutionIdempotencyRepository()
        execution_start_repository = InMemoryExecutionStartRepository(
            execution_repository,
            execution_idempotency_repository,
        )
        return (
            InMemoryWorkflowRepository(),
            InMemoryWorkflowVersionRepository(),
            execution_repository,
            execution_history_repository,
            execution_idempotency_repository,
            execution_start_repository,
        )

    connection_factory = postgres_connection_factory(database_url)
    with connection_factory() as connection:
        PostgresSchema.initialize(connection)

    execution_store = PostgresExecutionRepository(connection_factory, tenant_id=tenant_id)
    execution_history_repository = PostgresExecutionHistoryRepository(connection_factory, tenant_id=tenant_id)
    execution_repository = execution_store
    execution_idempotency_repository = PostgresExecutionIdempotencyRepository(
        connection_factory, tenant_id=tenant_id
    )
    execution_start_repository = PostgresExecutionStartRepository(
        connection_factory, tenant_id=tenant_id
    )

    return (
        PostgresWorkflowRepository(connection_factory, tenant_id=tenant_id),
        PostgresWorkflowVersionRepository(connection_factory, tenant_id=tenant_id),
        execution_repository,
        execution_history_repository,
        execution_idempotency_repository,
        execution_start_repository,
    )


def build_tenant_persistence(context: AuthorizationContext):
    """Build durable repository boundaries after an explicit authorization check."""
    if context.is_system:
        return _build_persistence()

    AuthorizationPolicy.require_tenant(context, context.tenant_id)
    if not os.environ.get("AUTOMATION_OS_DATABASE_URL"):
        raise RuntimeError(
            "Tenant-scoped persistence requires durable PostgreSQL configuration"
        )
    return _build_persistence(tenant_id=context.tenant_id.value)


(
    workflow_repository,
    workflow_version_repository,
    execution_repository,
    execution_history_repository,
    execution_idempotency_repository,
    execution_start_repository,
) = _build_persistence()


def _build_review_decision_repository():
    database_url = os.environ.get("AUTOMATION_OS_DATABASE_URL")
    if not database_url:
        return InMemoryReviewDecisionRepository()

    connection_factory = postgres_connection_factory(database_url)
    with connection_factory() as connection:
        PostgresSchema.initialize(connection)
    return PostgresReviewDecisionRepository(connection_factory)


review_decision_repository = _build_review_decision_repository()


def build_review_repositories(context: AuthorizationContext):
    """Build review repositories after explicit authorization context validation."""
    if not isinstance(context, AuthorizationContext):
        raise TypeError("context must be an AuthorizationContext")

    if context.is_system:
        return workflow_repository, review_decision_repository

    AuthorizationPolicy.require_tenant(context, context.tenant_id)
    if not os.environ.get("AUTOMATION_OS_DATABASE_URL"):
        raise RuntimeError(
            "Tenant-scoped review persistence requires durable PostgreSQL configuration"
        )

    connection_factory = postgres_connection_factory(
        os.environ["AUTOMATION_OS_DATABASE_URL"]
    )
    with connection_factory() as connection:
        PostgresSchema.initialize(connection)

    tenant_id = context.tenant_id.value
    return (
        PostgresWorkflowRepository(connection_factory, tenant_id=tenant_id),
        PostgresReviewDecisionRepository(connection_factory, tenant_id=tenant_id),
    )


capability_registry = CapabilityRegistry()
capability_provider_resolver = CapabilityProviderResolver(legacy_registry=capability_registry)

start_workflow_execution = StartWorkflowExecution(
    workflow_repository,
    execution_repository,
    idempotency_repository=execution_idempotency_repository,
    execution_start_repository=execution_start_repository,
    workflow_version_repository=workflow_version_repository,
)
execution_progress = GetExecutionProgress(execution_repository)
discover_executions = DiscoverExecutions(execution_repository)
cancel_execution = CancelExecution(execution_repository)
resume_execution = ResumeExecution(execution_repository)
retry_execution = RetryExecution(execution_repository)
start_retrying_execution = StartRetryingExecution(execution_repository)
step_executor = ExecuteWorkflowStep(
    workflow_repository,
    execution_repository,
    CapabilityDispatcher(capability_provider_resolver),
    ConditionEvaluator(),
    workflow_version_repository,
)
execute_workflow = ExecuteWorkflow(execution_repository, step_executor)
retry_and_execute_execution = RetryAndExecuteExecution(
    retry_execution,
    start_retrying_execution,
    execute_workflow,
)


def _build_runtime_connection_preparer(context: AuthorizationContext):
    """Compose runtime connection resolution inside an authorized tenant scope."""
    if context.is_system:
        return None

    AuthorizationPolicy.require_tenant(context, context.tenant_id)
    if not os.environ.get("AUTOMATION_OS_DATABASE_URL"):
        raise RuntimeError(
            "Tenant-scoped runtime connections require durable PostgreSQL configuration"
        )

    connection_factory = postgres_connection_factory(
        os.environ["AUTOMATION_OS_DATABASE_URL"]
    )
    with connection_factory() as connection:
        PostgresSchema.initialize(connection)

    connection_repository = PostgresConnectionRepository(
        connection_factory,
        tenant_id=context.tenant_id.value,
    )
    resolver = ConnectionResolver(connection_repository)
    runtime_resolver = ResolveRuntimeConnection(
        resolver,
        UnconfiguredSecretProvider(),
    )
    return PrepareWorkflowRuntimeConnections(runtime_resolver)

def _compose_execution_use_cases(
    workflow_repository,
    workflow_version_repository,
    execution_repository,
    execution_idempotency_repository,
    execution_start_repository,
    runtime_connection_preparer=None,
) -> ExecutionUseCases:
    start = StartWorkflowExecution(
        workflow_repository,
        execution_repository,
        idempotency_repository=execution_idempotency_repository,
        execution_start_repository=execution_start_repository,
        workflow_version_repository=workflow_version_repository,
    )
    progress = GetExecutionProgress(execution_repository)
    discovery = DiscoverExecutions(execution_repository)
    cancel = CancelExecution(execution_repository)
    resume = ResumeExecution(execution_repository)
    retry = RetryExecution(execution_repository)
    start_retrying = StartRetryingExecution(execution_repository)
    step = ExecuteWorkflowStep(
        workflow_repository,
        execution_repository,
        CapabilityDispatcher(capability_provider_resolver),
        ConditionEvaluator(),
        workflow_version_repository,
        runtime_connection_preparer=runtime_connection_preparer,
    )
    execute = ExecuteWorkflow(execution_repository, step)
    retry_and_execute = RetryAndExecuteExecution(
        retry,
        start_retrying,
        execute,
    )
    return ExecutionUseCases(
        start_workflow_execution=start,
        execution_progress=progress,
        discover_executions=discovery,
        cancel_execution=cancel,
        resume_execution=resume,
        retry_execution=retry,
        retry_and_execute_execution=retry_and_execute,
    )


def build_execution_use_cases(context: AuthorizationContext) -> ExecutionUseCases:
    """Compose execution services inside the caller's authorized persistence scope."""
    if not isinstance(context, AuthorizationContext):
        raise TypeError("context must be an AuthorizationContext")

    if context.is_system:
        return _compose_execution_use_cases(
            workflow_repository,
            workflow_version_repository,
            execution_repository,
            execution_idempotency_repository,
            execution_start_repository,
        )

    (
        scoped_workflow_repository,
        scoped_workflow_version_repository,
        scoped_execution_repository,
        _history_repository,
        scoped_idempotency_repository,
        scoped_start_repository,
    ) = build_tenant_persistence(context)

    runtime_connection_preparer = _build_runtime_connection_preparer(context)

    return _compose_execution_use_cases(
        scoped_workflow_repository,
        scoped_workflow_version_repository,
        scoped_execution_repository,
        scoped_idempotency_repository,
        scoped_start_repository,
        runtime_connection_preparer=runtime_connection_preparer,
    )
