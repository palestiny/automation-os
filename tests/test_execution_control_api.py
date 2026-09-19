from uuid import uuid4

import pytest
from fastapi import HTTPException

import app.api.execution as api
import app.core.execution_dependencies as deps
from app.application.capability import Capability
from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.execution_progress import GetExecutionProgress
from app.application.resume_execution import ResumeExecution
from app.application.retry_and_execute_execution import RetryAndExecuteExecution
from app.application.retry_execution import RetryExecution
from app.application.start_retrying_execution import StartRetryingExecution
from app.application.cancel_execution import CancelExecution
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


class SuccessfulCapability(Capability):
    def execute(self, context):
        from app.application.capability_result import CapabilityResult
        return CapabilityResult.success()


@pytest.fixture
def isolated_dependencies(monkeypatch):
    executions = InMemoryExecutionRepository()
    workflows = InMemoryWorkflowRepository()
    registry = CapabilityRegistry()

    progress = GetExecutionProgress(executions)
    cancel = CancelExecution(executions)
    resume = ResumeExecution(executions)
    retry = RetryExecution(executions)
    step_executor = ExecuteWorkflowStep(
        workflows,
        executions,
        CapabilityDispatcher(registry),
        ConditionEvaluator(),
    )
    execute_workflow = ExecuteWorkflow(executions, step_executor)
    retry_and_execute = RetryAndExecuteExecution(
        retry,
        StartRetryingExecution(executions),
        execute_workflow,
    )

    monkeypatch.setattr(api, "execution_repository", executions)
    monkeypatch.setattr(api, "execution_progress", progress)
    monkeypatch.setattr(api, "cancel_execution", cancel)
    monkeypatch.setattr(api, "resume_execution", resume)
    monkeypatch.setattr(api, "retry_execution", retry)
    monkeypatch.setattr(api, "retry_and_execute_execution", retry_and_execute)

    return executions, workflows, registry


def test_get_execution_returns_projection(isolated_dependencies):
    executions, _, _ = isolated_dependencies
    execution = Execution.create(uuid4())
    executions.save(execution)

    result = api.get_execution(execution.id)

    assert result.execution_id == execution.id
    assert result.state is ExecutionState.CREATED
    assert result.attempt == 1


def test_get_execution_returns_404_for_missing_execution(isolated_dependencies):
    with pytest.raises(HTTPException) as error:
        api.get_execution(uuid4())

    assert error.value.status_code == 404


def test_cancel_endpoint_delegates_to_application_boundary(isolated_dependencies):
    executions, _, _ = isolated_dependencies
    execution = Execution.create(uuid4())
    executions.save(execution)

    result = api.cancel_execution_endpoint(execution.id)

    assert result.state is ExecutionState.CANCELLED


def test_resume_endpoint_delegates_to_application_boundary(isolated_dependencies):
    executions, _, _ = isolated_dependencies
    execution = Execution.create(uuid4())
    execution.start()
    execution.wait()
    executions.save(execution)

    result = api.resume_execution_endpoint(execution.id)

    assert result.state is ExecutionState.RUNNING


def test_retry_endpoint_delegates_to_application_boundary(isolated_dependencies):
    executions, _, _ = isolated_dependencies
    execution = Execution.create(uuid4())
    execution.start()
    execution.fail()
    executions.save(execution)

    result = api.retry_execution_endpoint(execution.id)

    assert result.state is ExecutionState.RETRYING
    assert result.attempt == 2


def test_invalid_cancel_maps_to_conflict(isolated_dependencies):
    executions, _, _ = isolated_dependencies
    execution = Execution.create(uuid4())
    execution.start()
    execution.fail()
    executions.save(execution)

    with pytest.raises(HTTPException) as error:
        api.cancel_execution_endpoint(execution.id)

    assert error.value.status_code == 409


def test_retry_and_execute_endpoint_composes_runtime(isolated_dependencies):
    executions, workflows, registry = isolated_dependencies
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Step", "success")],
    )
    workflows.save(workflow)
    registry.register("success", SuccessfulCapability())

    execution = Execution.create(workflow.id)
    execution.start()
    execution.fail()
    executions.save(execution)

    result = api.retry_and_execute_endpoint(execution.id)

    assert result.state is ExecutionState.COMPLETED
    assert result.attempt == 2
    assert result.current_step == 1
