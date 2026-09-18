from uuid import uuid4

import pytest

from app.application.workflow_start_request import WorkflowStartRequest
from app.application.workflow_start_service import WorkflowStartService
from app.domain.execution import Execution
from app.domain.workflow import Workflow, WorkflowStep


class FakeWorkflowResolver:
    def __init__(self, workflow=None):
        self.workflow = workflow
        self.requested_workflow_id = None

    def get_by_id(self, workflow_id):
        self.requested_workflow_id = workflow_id
        return self.workflow


class FakeOrchestrator:
    def __init__(self):
        self.started_workflow = None
        self.execution = Execution.create(uuid4())

    def start(self, workflow):
        self.started_workflow = workflow
        return self.execution


def make_workflow():
    return Workflow.create(
        name="Publishing Pipeline",
        steps=[WorkflowStep.create(name="Publish", capability="publish")],
    )


def test_workflow_start_service_resolves_workflow_and_delegates_to_orchestrator():
    workflow = make_workflow()
    resolver = FakeWorkflowResolver(workflow)
    orchestrator = FakeOrchestrator()
    service = WorkflowStartService(resolver, orchestrator)
    request = WorkflowStartRequest(workflow_id=workflow.id)

    execution = service.start(request)

    assert resolver.requested_workflow_id == workflow.id
    assert orchestrator.started_workflow is workflow
    assert execution is orchestrator.execution


def test_workflow_start_service_rejects_unknown_workflow():
    resolver = FakeWorkflowResolver()
    orchestrator = FakeOrchestrator()
    service = WorkflowStartService(resolver, orchestrator)
    request = WorkflowStartRequest(workflow_id=uuid4())

    with pytest.raises(ValueError, match="Workflow was not found"):
        service.start(request)

    assert orchestrator.started_workflow is None
