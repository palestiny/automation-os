from __future__ import annotations

import os

from app.application.authorization import AuthorizationContext, AuthorizationPolicy
from app.application.cancel_execution import CancelExecution
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
)
from app.infrastructure.persistence.postgres import (
    PostgresExecutionHistoryRepository,
    PostgresExecutionIdempotencyRepository,
    PostgresExecutionRepository,
    PostgresExecutionStartRepository,
    PostgresSchema,
    PostgresWorkflowRepository,
    PostgresWorkflowVersionRepository,
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
    execution_repository = EventRecordingExecutionRepository(
        execution_store,
        execution_history_repository,
    )
    execution_idempotency_repository = PostgresExecutionIdempotencyRepository(
        connection_factory, tenant_id=tenant_id
    )
    execution_start_repository = PostgresExecutionStartRepository(
        connection_factory, tenant_id=tenant_id
    )

    return (
        PostgresWorkflowRepository(connection_factory, tenant_id=tenant_id),
        PostgresWorkflowVersionRepository(connection_factory),
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

_step_executor = ExecuteWorkflowStep(
    workflow_repository,
    execution_repository,
    CapabilityDispatcher(capability_provider_resolver),
    ConditionEvaluator(),
    workflow_version_repository,
)
_execute_workflow = ExecuteWorkflow(execution_repository, _step_executor)
retry_and_execute_execution = RetryAndExecuteExecution(
    retry_execution,
    StartRetryingExecution(execution_repository),
    _execute_workflow,
)
