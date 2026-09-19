from uuid import uuid4

import pytest

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.resume_and_execute_execution import ResumeAndExecuteExecution
from app.application.resume_execution import ResumeExecution
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


class RecordingCapability:
    def __init__(self, failure: Exception | None = None) -> None:
        self.calls = 0
        self.failure = failure

    def execute(self, context: ExecutionContext) -> CapabilityResult:
        self.calls += 1
        if self.failure is not None:
            return CapabilityResult.failure(self.failure)
        return CapabilityResult.success()


def build_use_case(workflow: Workflow, execution: Execution, capability) -> ResumeAndExecuteExecution:
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
    orchestrator = ExecuteWorkflow(executions, step_executor)
    return ResumeAndExecuteExecution(
        ResumeExecution(executions),
        orchestrator,
    )


def waiting_execution(workflow: Workflow) -> Execution:
    execution = Execution.create(workflow.id)
    execution.start()
    execution.wait()
    return execution


def test_resume_and_execute_completes_workflow():
    workflow = Workflow.create("Pipeline", [WorkflowStep.create("Step", "step")])
    execution = waiting_execution(workflow)
    capability = RecordingCapability()

    use_case = build_use_case(workflow, execution, capability)

    result = use_case.execute(execution.id)

    assert result is execution
    assert result.state is ExecutionState.COMPLETED
    assert result.current_step == 1
    assert capability.calls == 1


def test_resume_and_execute_propagates_failure_after_resume():
    workflow = Workflow.create("Pipeline", [WorkflowStep.create("Step", "step")])
    execution = waiting_execution(workflow)
    capability = RecordingCapability(RuntimeError("provider unavailable"))

    use_case = build_use_case(workflow, execution, capability)

    with pytest.raises(ValueError, match="Capability execution failed"):
        use_case.execute(execution.id)

    assert execution.state is ExecutionState.FAILED
    assert execution.current_step == 0


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.CREATED,
        ExecutionState.RUNNING,
        ExecutionState.RETRYING,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    ],
)
def test_resume_and_execute_requires_waiting_execution(state):
    workflow = Workflow.create("Pipeline", [WorkflowStep.create("Step", "step")])
    execution = Execution.create(workflow.id)

    if state is ExecutionState.RUNNING:
        execution.start()
    elif state is ExecutionState.RETRYING:
        execution.start()
        execution.fail()
        execution.retry()
    elif state is ExecutionState.COMPLETED:
        execution.start()
        execution.complete()
    elif state is ExecutionState.FAILED:
        execution.start()
        execution.fail()
    elif state is ExecutionState.CANCELLED:
        execution.cancel()

    use_case = build_use_case(workflow, execution, RecordingCapability())

    with pytest.raises(ValueError, match="resume|WAITING"):
        use_case.execute(execution.id)

    assert execution.state is state
