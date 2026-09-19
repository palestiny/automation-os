from uuid import uuid4

import pytest

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.execution_context import ExecutionContext
from app.application.retry_execution import RetryExecution
from app.application.retry_and_execute_execution import RetryAndExecuteExecution
from app.application.start_retrying_execution import StartRetryingExecution
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


class RecordingCapability:
    def __init__(self, failure=None):
        self.calls = 0
        self.failure = failure

    def execute(self, context):
        self.calls += 1
        if self.failure is not None:
            return CapabilityResult.failure(self.failure)
        return CapabilityResult.success()


def failed_execution(workflow):
    execution = Execution.create(workflow.id)
    execution.start()
    execution.fail()
    return execution


def build_use_case(workflow, execution, capability):
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)
    executions.save(execution)

    registry = CapabilityRegistry()
    registry.register("step", capability)
    step_executor = ExecuteWorkflowStep(
        workflows,
        executions,
        CapabilityDispatcher(registry),
        ConditionEvaluator(),
    )
    return RetryAndExecuteExecution(
        RetryExecution(executions),
        StartRetryingExecution(executions),
        ExecuteWorkflow(executions, step_executor),
    )


def test_retry_and_execute_completes_workflow():
    workflow = Workflow.create("Pipeline", [WorkflowStep.create("Step", "step")])
    execution = failed_execution(workflow)
    capability = RecordingCapability()

    use_case = build_use_case(workflow, execution, capability)

    result = use_case.execute(execution.id)

    assert result is execution
    assert result.state is ExecutionState.COMPLETED
    assert result.attempt == 2
    assert result.current_step == 1
    assert capability.calls == 1


def test_retry_and_execute_propagates_failure():
    workflow = Workflow.create("Pipeline", [WorkflowStep.create("Step", "step")])
    execution = failed_execution(workflow)
    capability = RecordingCapability(RuntimeError("provider unavailable"))

    use_case = build_use_case(workflow, execution, capability)

    with pytest.raises(ValueError, match="Capability execution failed"):
        use_case.execute(execution.id)

    assert execution.state is ExecutionState.FAILED
    assert execution.attempt == 2


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.CREATED,
        ExecutionState.RUNNING,
        ExecutionState.WAITING,
        ExecutionState.RETRYING,
        ExecutionState.COMPLETED,
        ExecutionState.CANCELLED,
    ],
)
def test_retry_and_execute_requires_failed_execution(state):
    workflow = Workflow.create("Pipeline", [WorkflowStep.create("Step", "step")])
    execution = Execution(
        id=uuid4(),
        workflow_id=workflow.id,
        current_step=0,
        state=state,
        attempt=1,
    )
    use_case = build_use_case(workflow, execution, RecordingCapability())

    with pytest.raises(ValueError, match="retry"):
        use_case.execute(execution.id)

    assert execution.state is state
