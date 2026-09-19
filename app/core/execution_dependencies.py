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
)

job_manager = JobManager()

_execution_store = InMemoryExecutionRepository()
execution_history_repository = InMemoryExecutionHistoryRepository()
execution_repository = EventRecordingExecutionRepository(
    _execution_store,
    execution_history_repository,
)
execution_idempotency_repository = InMemoryExecutionIdempotencyRepository()
execution_start_repository = InMemoryExecutionStartRepository(
    execution_repository,
    execution_idempotency_repository,
)
workflow_repository = InMemoryWorkflowRepository()
capability_registry = CapabilityRegistry()
capability_provider_resolver = CapabilityProviderResolver(legacy_registry=capability_registry)

start_workflow_execution = StartWorkflowExecution(
    workflow_repository,
    execution_repository,
    idempotency_repository=execution_idempotency_repository,
    execution_start_repository=execution_start_repository,
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
)
_execute_workflow = ExecuteWorkflow(execution_repository, _step_executor)
retry_and_execute_execution = RetryAndExecuteExecution(
    retry_execution,
    StartRetryingExecution(execution_repository),
    _execute_workflow,
)
