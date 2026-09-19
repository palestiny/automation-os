from fastapi.testclient import TestClient

from app.domain.workflow import Workflow, WorkflowStep, WorkflowParameter
from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository
from app.main import app
import app.api.workflow as workflow_api


def make_workflow(
    name: str,
    goal: str,
    publish: bool = True,
    automation_domain: str | None = None,
    discovery_tags: list[str] | None = None,
) -> Workflow:
    workflow = Workflow.create(
        name=name,
        steps=[WorkflowStep.create(name="Run", capability="test")],
        supported_goals=[goal],
        required_parameters=["source"],
        parameter_types=[WorkflowParameter.create("source", "string")],
        automation_domain=automation_domain,
        discovery_tags=discovery_tags,
    )
    if publish:
        workflow.publish()
    return workflow


def with_repository(repository):
    original = workflow_api.workflow_repository
    workflow_api.workflow_repository = repository
    workflow_api.list_workflows = workflow_api.ListWorkflows(repository)
    return original


def restore_repository(original):
    workflow_api.workflow_repository = original
    workflow_api.list_workflows = workflow_api.ListWorkflows(original)


def test_get_workflows_returns_published_workflows():
    repository = InMemoryWorkflowRepository()
    published = make_workflow("Published", "create_short_video")
    draft = make_workflow("Draft", "create_short_video", publish=False)
    repository.save(published)
    repository.save(draft)

    original = with_repository(repository)
    try:
        response = TestClient(app).get("/workflows")
    finally:
        restore_repository(original)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Published"]


def test_get_workflows_filters_by_goal():
    repository = InMemoryWorkflowRepository()
    repository.save(make_workflow("Video", "create_short_video"))
    repository.save(make_workflow("Publish", "publish_content"))

    original = with_repository(repository)
    try:
        response = TestClient(app).get("/workflows?goal=publish_content")
    finally:
        restore_repository(original)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Publish"]


def test_get_workflows_filters_by_automation_domain():
    repository = InMemoryWorkflowRepository()
    repository.save(
        make_workflow(
            "Content",
            "create_short_video",
            automation_domain="content",
            discovery_tags=["video", "short-form"],
        )
    )
    repository.save(
        make_workflow(
            "Reporting",
            "generate_report",
            automation_domain="business_reporting",
            discovery_tags=["reporting"],
        )
    )

    original = with_repository(repository)
    try:
        response = TestClient(app).get("/workflows?automation_domain=content")
    finally:
        restore_repository(original)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Content"]


def test_get_workflows_filters_by_all_repeated_tags():
    repository = InMemoryWorkflowRepository()
    repository.save(
        make_workflow(
            "Video",
            "create_short_video",
            discovery_tags=["video", "short-form"],
        )
    )
    repository.save(
        make_workflow(
            "Reporting",
            "generate_report",
            discovery_tags=["reporting"],
        )
    )

    original = with_repository(repository)
    try:
        response = TestClient(app).get(
            "/workflows?tag=video&tag=short-form"
        )
    finally:
        restore_repository(original)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Video"]


def test_get_workflows_exposes_discovery_metadata():
    repository = InMemoryWorkflowRepository()
    repository.save(
        make_workflow(
            "Video",
            "create_short_video",
            automation_domain="content",
            discovery_tags=["video", "short-form"],
        )
    )

    original = with_repository(repository)
    try:
        response = TestClient(app).get("/workflows")
    finally:
        restore_repository(original)

    assert response.status_code == 200
    assert response.json()[0]["automation_domain"] == "content"
    assert response.json()[0]["discovery_tags"] == ["video", "short-form"]


def test_get_workflows_does_not_execute_workflows():
    repository = InMemoryWorkflowRepository()
    repository.save(make_workflow("Video", "create_short_video"))

    original = with_repository(repository)
    try:
        response = TestClient(app).get("/workflows")
    finally:
        restore_repository(original)

    assert response.status_code == 200
    assert response.json()[0]["required_parameters"] == ["source"]
