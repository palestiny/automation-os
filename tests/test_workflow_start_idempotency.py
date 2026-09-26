from uuid import uuid4

import pytest

from app.application.create_workflow_version import CreateWorkflowVersion
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionIdempotencyRepository,
    InMemoryExecutionRepository,
    InMemoryExecutionStartRepository,
    InMemoryWorkflowRepository,
    InMemoryWorkflowVersionRepository,
)


def published_workflow(name: str = "Pipeline") -> Workflow:
    workflow = Workflow.create(
        name,
        [WorkflowStep.create("Step 1", "test")],
    )
    workflow.publish()
    return workflow


def build_start():
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    idempotency = InMemoryExecutionIdempotencyRepository()
    execution_start = InMemoryExecutionStartRepository(executions, idempotency)
    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=execution_start,
    )
    return workflows, executions, idempotency, start


def test_idempotent_start_replays_the_same_execution_and_persists_only_once():
    workflows, executions, _, start = build_start()
    workflow = published_workflow()
    workflows.save(workflow)

    first = start.execute(workflow.id, idempotency_key=" request-1 ")
    replay = start.execute(workflow.id, idempotency_key="request-1")

    assert replay is first
    assert executions.all() == (first,)


def test_idempotency_key_conflict_across_workflows_does_not_create_second_execution():
    workflows, executions, _, start = build_start()
    first_workflow = published_workflow("First")
    second_workflow = published_workflow("Second")
    workflows.save(first_workflow)
    workflows.save(second_workflow)

    first = start.execute(first_workflow.id, idempotency_key="request-1")

    with pytest.raises(ValueError, match="different workflow"):
        start.execute(second_workflow.id, idempotency_key="request-1")

    assert executions.all() == (first,)


def test_orphaned_idempotency_record_is_explicit_failure():
    workflows, executions, idempotency, start = build_start()
    workflow = published_workflow()
    workflows.save(workflow)
    idempotency.reserve("request-1", workflow.id, uuid4())

    with pytest.raises(RuntimeError, match="missing execution"):
        start.execute(workflow.id, idempotency_key="request-1")

    assert executions.all() == ()


def test_idempotent_start_requires_both_idempotency_and_atomic_start_boundaries():
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflow = published_workflow()
    workflows.save(workflow)

    with pytest.raises(RuntimeError, match="no idempotency repository"):
        StartWorkflowExecution(workflows, executions).execute(
            workflow.id,
            idempotency_key="request-1",
        )

    idempotency = InMemoryExecutionIdempotencyRepository()
    with pytest.raises(RuntimeError, match="Atomic execution-start persistence"):
        StartWorkflowExecution(
            workflows,
            executions,
            idempotency_repository=idempotency,
        ).execute(
            workflow.id,
            idempotency_key="request-1",
        )

    assert executions.all() == ()


def test_idempotent_replay_returns_original_execution_when_explicit_version_differs():
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    idempotency = InMemoryExecutionIdempotencyRepository()
    execution_start = InMemoryExecutionStartRepository(executions, idempotency)
    versions = InMemoryWorkflowVersionRepository()
    start = StartWorkflowExecution(
        workflows,
        executions,
        idempotency_repository=idempotency,
        execution_start_repository=execution_start,
        workflow_version_repository=versions,
    )

    workflow = published_workflow()
    workflows.save(workflow)

    first_version = CreateWorkflowVersion(workflows, versions).execute(workflow.id)
    first_version.publish()
    versions.save(first_version)

    second_version = CreateWorkflowVersion(workflows, versions).execute(workflow.id)
    second_version.publish()
    versions.save(second_version)

    first = start.execute(
        workflow.id,
        idempotency_key="request-version-replay",
        workflow_version_id=first_version.id,
    )
    replay = start.execute(
        workflow.id,
        idempotency_key="request-version-replay",
        workflow_version_id=second_version.id,
    )

    assert replay is first
    assert replay.workflow_version_id == first_version.id
    assert executions.all() == (first,)
