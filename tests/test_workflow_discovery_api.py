from fastapi.testclient import TestClient

from app.domain.workflow import Workflow, WorkflowStep, WorkflowParameter
from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository
from app.main import app
import app.api.workflow as workflow_api


def make_workflow(name: str, goal: str, publish: bool = True) -> Workflow:
    workflow = Workflow.create(
        name=name,
        steps=[WorkflowStep.create(name="Run", capability="test")],
        supported_goals=[goal],
        required_parameters=["source"],
        parameter_types=[WorkflowParameter.create("source", "string")],
    )
    if publish:
        workflow.publish()
    return workflow


def test_get_workflows_returns_published_workflows():
    repository = InMemoryWorkflowRepository()
    published = make_workflow("Published", "create_short_video")
    draft = make_workflow("Draft", "create_short_video", publish=False)
    repository.save(published)
    repository.save(draft)

    original = workflow_api.workflow_repository
    workflow_api.workflow_repository = repository
    workflow_api.list_workflows = workflow_api.ListWorkflows(repository)
    try:
        response = TestClient(app).get("/workflows")
    finally:
        workflow_api.workflow_repository = original
        workflow_api.list_workflows = workflow_api.ListWorkflows(original)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Published"]


def test_get_workflows_filters_by_goal():
    repository = InMemoryWorkflowRepository()
    repository.save(make_workflow("Video", "create_short_video"))
    repository.save(make_workflow("Publish", "publish_content"))

    original = workflow_api.workflow_repository
    workflow_api.workflow_repository = repository
    workflow_api.list_workflows = workflow_api.ListWorkflows(repository)
    try:
        response = TestClient(app).get("/workflows?goal=publish_content")
    finally:
        workflow_api.workflow_repository = original
        workflow_api.list_workflows = workflow_api.ListWorkflows(original)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Publish"]


def test_get_workflows_does_not_execute_workflows():
    repository = InMemoryWorkflowRepository()
    repository.save(make_workflow("Video", "create_short_video"))

    original = workflow_api.workflow_repository
    workflow_api.workflow_repository = repository
    workflow_api.list_workflows = workflow_api.ListWorkflows(repository)
    try:
        response = TestClient(app).get("/workflows")
    finally:
        workflow_api.workflow_repository = original
        workflow_api.list_workflows = workflow_api.ListWorkflows(original)

    assert response.status_code == 200
    assert response.json()[0]["required_parameters"] == ["source"]
