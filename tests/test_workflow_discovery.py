import pytest

from app.application.workflow_discovery import (
    DiscoverWorkflows,
    WorkflowDiscoveryQuery,
)
from app.domain.workflow import Workflow, WorkflowStep


def workflow(name: str, goal: str, published: bool = True) -> Workflow:
    item = Workflow.create(
        name=name,
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=[goal],
    )
    if published:
        item.publish()
    return item


def test_discovery_returns_published_workflows_for_goal():
    first = workflow("First", "create_short_video")
    second = workflow("Second", "publish_content")

    result = DiscoverWorkflows([first, second]).execute(
        WorkflowDiscoveryQuery(goal="create_short_video")
    )

    assert result == (first,)


def test_discovery_excludes_draft_workflows():
    draft = workflow("Draft", "create_short_video", published=False)

    result = DiscoverWorkflows([draft]).execute(
        WorkflowDiscoveryQuery(goal="create_short_video")
    )

    assert result == ()


def test_discovery_without_goal_returns_all_published_workflows():
    first = workflow("First", "create_short_video")
    second = workflow("Second", "publish_content")
    draft = workflow("Draft", "publish_content", published=False)

    result = DiscoverWorkflows([first, second, draft]).execute(
        WorkflowDiscoveryQuery()
    )

    assert result == (first, second)


def test_discovery_unknown_goal_returns_empty():
    item = workflow("First", "create_short_video")

    assert DiscoverWorkflows([item]).execute(
        WorkflowDiscoveryQuery(goal="unknown")
    ) == ()


def test_discovery_rejects_empty_goal():
    with pytest.raises(ValueError, match="cannot be empty"):
        WorkflowDiscoveryQuery(goal="   ")


def test_discovery_rejects_invalid_query():
    with pytest.raises(TypeError):
        DiscoverWorkflows([]).execute(None)


def test_discovery_rejects_invalid_workflow():
    with pytest.raises(ValueError, match="Workflow"):
        DiscoverWorkflows([object()])
