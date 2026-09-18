from __future__ import annotations

import pytest

from app.application.intent_analysis import IntentAnalyzer
from app.application.request_execution import ExecuteRequest
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.execution import ExecutionState
from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


class FakeAnalyzer:
    def __init__(self, intent=None, error=None):
        self.intent = intent
        self.error = error
        self.requests = []

    def analyze(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.intent


def published_workflow(goal):
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Step 1", "test")],
        supported_goals=[goal],
    )
    workflow.publish()
    return workflow


def build_use_case(workflows, analyzer):
    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()
    for workflow in workflows:
        workflow_repository.save(workflow)

    return (
        ExecuteRequest(
            analyzer=analyzer,
            execute_intent=__import__(
                "app.application.intent_execution",
                fromlist=["ExecuteIntent"],
            ).ExecuteIntent(
                workflows,
                StartWorkflowExecution(workflow_repository, execution_repository),
            ),
        ),
        execution_repository,
    )


def test_request_flows_from_analysis_to_execution():
    workflow = published_workflow("create_short_video")
    analyzer = FakeAnalyzer(Intent.create("create_short_video", {"source": "youtube"}))
    use_case, executions = build_use_case([workflow], analyzer)

    result = use_case.execute("Turn this into a short")

    assert result.execution is not None
    assert result.execution.workflow_id == workflow.id
    assert result.execution.state is ExecutionState.RUNNING
    assert analyzer.requests == ["Turn this into a short"]


def test_analysis_failure_stops_before_execution():
    analyzer = FakeAnalyzer(error=RuntimeError("provider unavailable"))
    use_case, executions = build_use_case([], analyzer)

    with pytest.raises(RuntimeError, match="provider unavailable"):
        use_case.execute("Do something")

    assert executions.all() == []


def test_no_match_remains_explicit():
    workflow = published_workflow("publish_content")
    analyzer = FakeAnalyzer(Intent.create("create_short_video"))
    use_case, executions = build_use_case([workflow], analyzer)

    result = use_case.execute("Create a short")

    assert result.execution is None
    assert result.status.value == "no_match"
    assert executions.all() == []


def test_execute_request_requires_analyzer():
    with pytest.raises(TypeError):
        ExecuteRequest(None, None)
