from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.scheduled_workflow_execution import ExecuteDueWorkflow, StartDueWorkflowExecution
from app.application.scheduling import FixedClock, ScheduledExecutionRequest
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.condition_evaluator import ConditionEvaluator
from app.domain.execution import ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


class RecordingCapability:
    def __init__(self, name: str, calls: list[str]) -> None:
        self.name = name
        self.calls = calls

    def execute(self, context: ExecutionContext) -> CapabilityResult:
        self.calls.append(self.name)
        return CapabilityResult.success()


def published_workflow() -> Workflow:
    workflow = Workflow.create(
        "Scheduled Pipeline",
        [
            WorkflowStep.create("Step 1", "first"),
            WorkflowStep.create("Step 2", "second"),
        ],
    )
    workflow.publish()
    return workflow


def build_use_case(workflow: Workflow, calls: list[str]):
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)

    registry = CapabilityRegistry()
    registry.register("first", RecordingCapability("first", calls))
    registry.register("second", RecordingCapability("second", calls))

    step_executor = ExecuteWorkflowStep(
        workflows,
        executions,
        CapabilityDispatcher(registry),
        ConditionEvaluator(),
    )
    orchestrator = ExecuteWorkflow(executions, step_executor)
    return workflows, executions, StartDueWorkflowExecution, orchestrator


def test_due_scheduled_workflow_runs_to_completion():
    workflow = published_workflow()
    calls: list[str] = []
    workflows, executions, start_due_type, orchestrator = build_use_case(workflow, calls)

    from app.application.start_workflow_execution import StartWorkflowExecution

    start_due = start_due_type(
        StartWorkflowExecution(workflows, executions),
        FixedClock(datetime(2026, 9, 19, 20, 0, tzinfo=timezone.utc)),
    )
    request = ScheduledExecutionRequest.create(
        workflow.id,
        datetime(2026, 9, 19, 20, 0, tzinfo=timezone.utc),
    )

    started = start_due.execute(request)
    assert started is not None
    result = ExecuteDueWorkflow(start_due, orchestrator).execute(request)

    assert result is not None
    assert result.state is ExecutionState.COMPLETED
    assert calls == ["first", "second"]


def test_future_scheduled_workflow_is_not_started_or_executed():
    workflow = published_workflow()
    calls: list[str] = []
    workflows, executions, start_due_type, orchestrator = build_use_case(workflow, calls)

    from app.application.start_workflow_execution import StartWorkflowExecution

    start_due = start_due_type(
        StartWorkflowExecution(workflows, executions),
        FixedClock(datetime(2026, 9, 19, 19, 59, tzinfo=timezone.utc)),
    )
    request = ScheduledExecutionRequest.create(
        workflow.id,
        datetime(2026, 9, 19, 20, 0, tzinfo=timezone.utc),
    )

    assert start_due.execute(request) is None
    assert calls == []


def test_due_scheduled_workflow_propagates_execution_failure():
    workflow = published_workflow()
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)

    class FailingCapability:
        def execute(self, context: ExecutionContext) -> CapabilityResult:
            return CapabilityResult.failure("boom")

    registry = CapabilityRegistry()
    registry.register("first", FailingCapability())
    registry.register("second", RecordingCapability("second", []))

    step_executor = ExecuteWorkflowStep(
        workflows,
        executions,
        CapabilityDispatcher(registry),
        ConditionEvaluator(),
    )
    orchestrator = ExecuteWorkflow(executions, step_executor)

    from app.application.start_workflow_execution import StartWorkflowExecution

    start_due = StartDueWorkflowExecution(
        StartWorkflowExecution(workflows, executions),
        FixedClock(datetime(2026, 9, 19, 20, 0, tzinfo=timezone.utc)),
    )
    request = ScheduledExecutionRequest.create(
        workflow.id,
        datetime(2026, 9, 19, 20, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError, match="Capability execution failed"):
        ExecuteDueWorkflow(start_due, orchestrator).execute(request)

    failed = next(iter(executions._executions.values()))
    assert failed.state is ExecutionState.FAILED
