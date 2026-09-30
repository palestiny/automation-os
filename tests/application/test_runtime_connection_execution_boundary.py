from uuid import uuid4

import pytest

from app.application.condition_evaluator import ConditionEvaluator
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.execution_context import ExecutionContext
from app.domain.execution import Execution
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
    InMemoryWorkflowVersionRepository,
)


def test_connection_preparation_failure_prevents_capability_invocation():
    tenant_id = uuid4()
    workflow = Workflow.create(
        name="publish",
        steps=[WorkflowStep.create(name="publish", capability="youtube.publish")],
        tenant_id=tenant_id,
    )
    version = WorkflowVersion.create_from_workflow(
        workflow,
        1,
        tenant_id=tenant_id,
    )
    version.publish()

    workflow_repository = InMemoryWorkflowRepository(tenant_id=tenant_id)
    workflow_repository.save(workflow)
    version_repository = InMemoryWorkflowVersionRepository(tenant_id=tenant_id)
    version_repository.save(version)

    execution_repository = InMemoryExecutionRepository()
    execution = Execution.create(
        workflow.id,
        workflow_version_id=version.id,
        tenant_id=tenant_id,
    )
    execution.start()
    execution_repository.save(execution)

    capability_calls = []

    class Dispatcher:
        def dispatch(self, capability_id, context):
            capability_calls.append(capability_id)
            return object()

    class FailingPreparer:
        def prepare(self, **kwargs):
            raise RuntimeError("Protected secret resolution failed")

    executor = ExecuteWorkflowStep(
        workflow_repository,
        execution_repository,
        Dispatcher(),
        ConditionEvaluator(),
        version_repository,
        FailingPreparer(),
    )

    with pytest.raises(RuntimeError, match="Protected secret resolution failed"):
        executor.execute(execution.id, ExecutionContext())

    assert capability_calls == []
    assert execution_repository.get(execution.id).state.value == "failed"
