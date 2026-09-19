from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.intent_execution import (
    ExecuteIntent,
    IntentExecutionStatus,
)
from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.workflow_selection import WorkflowSelectionStatus
from app.domain.intent import Intent
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository, InMemoryWorkflowRepository
from app.domain.workflow import Workflow, WorkflowStep


def make_workflow(goal: str) -> Workflow:
    workflow = Workflow.create(
        name="Content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=[goal],
    )
    workflow.publish()
    return workflow


def test_execute_intent_starts_selected_workflow():
    workflow = make_workflow("create_short_video")
    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()
    workflow_repository.save(workflow)

    use_case = ExecuteIntent(
        workflows=[workflow],
        start_workflow_execution=StartWorkflowExecution(
            workflow_repository,
            execution_repository,
        ),
    )

    result = use_case.execute(Intent.create("create_short_video"))

    assert result.status == IntentExecutionStatus.STARTED
    assert result.execution is not None
    assert result.execution.workflow_id == workflow.id


def test_execute_intent_does_not_start_when_no_workflow_matches():
    workflow = make_workflow("publish_content")
    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()
    workflow_repository.save(workflow)

    use_case = ExecuteIntent(
        workflows=[workflow],
        start_workflow_execution=StartWorkflowExecution(
            workflow_repository,
            execution_repository,
        ),
    )

    result = use_case.execute(Intent.create("create_short_video"))

    assert result.status == IntentExecutionStatus.NO_MATCH
    assert result.execution is None
    assert execution_repository.get(uuid4()) is None


def test_execute_intent_does_not_start_when_selection_is_ambiguous():
    first = make_workflow("create_short_video")
    second = make_workflow("create_short_video")
    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()
    workflow_repository.save(first)
    workflow_repository.save(second)

    use_case = ExecuteIntent(
        workflows=[first, second],
        start_workflow_execution=StartWorkflowExecution(
            workflow_repository,
            execution_repository,
        ),
    )

    result = use_case.execute(Intent.create("create_short_video"))

    assert result.status == IntentExecutionStatus.CLARIFICATION_REQUIRED
    assert result.execution is None
    assert execution_repository.get(uuid4()) is None


def test_execute_intent_does_not_start_unpublished_matching_workflow():
    workflow = Workflow.create(
        name="Draft content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=["create_short_video"],
    )
    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()
    workflow_repository.save(workflow)

    use_case = ExecuteIntent(
        workflows=[workflow],
        start_workflow_execution=StartWorkflowExecution(
            workflow_repository,
            execution_repository,
        ),
    )

    result = use_case.execute(Intent.create("create_short_video"))

    assert result.status == IntentExecutionStatus.NO_MATCH
    assert result.execution is None


def test_execute_intent_requires_start_workflow_execution():
    with pytest.raises(TypeError):
        ExecuteIntent(workflows=[], start_workflow_execution=None)


def test_execute_intent_does_not_start_when_parameters_are_missing():
    workflow = Workflow.create(
        name="Reporting workflow",
        steps=[WorkflowStep.create(name="Run", capability="report")],
        supported_goals=["generate_report"],
        required_parameters=["source"],
    )
    workflow.publish()
    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()
    workflow_repository.save(workflow)

    use_case = ExecuteIntent(
        workflows=[workflow],
        start_workflow_execution=StartWorkflowExecution(
            workflow_repository,
            execution_repository,
        ),
    )

    result = use_case.execute(Intent.create("generate_report"))

    assert result.status == IntentExecutionStatus.CLARIFICATION_REQUIRED
    assert result.execution is None


def test_execute_intent_returns_clarification_when_parameters_are_missing():
    workflow = Workflow.create(
        name="Reporting workflow",
        steps=[WorkflowStep.create(name="Run", capability="report")],
        supported_goals=["generate_report"],
        required_parameters=["source"],
    )
    workflow.publish()
    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()
    workflow_repository.save(workflow)

    use_case = ExecuteIntent(
        workflows=[workflow],
        start_workflow_execution=StartWorkflowExecution(
            workflow_repository,
            execution_repository,
        ),
    )

    result = use_case.execute(Intent.create("generate_report"))

    assert result.status == IntentExecutionStatus.CLARIFICATION_REQUIRED
    assert result.missing_parameters == ("source",)
    assert result.execution is None
