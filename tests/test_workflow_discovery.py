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


def test_discovery_filters_by_automation_domain():
    first = Workflow.create(
        name="Content",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=["create_short_video"],
        automation_domain="content",
    )
    second = Workflow.create(
        name="Reporting",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=["generate_report"],
        automation_domain="business_reporting",
    )
    first.publish()
    second.publish()

    result = DiscoverWorkflows([first, second]).execute(
        WorkflowDiscoveryQuery(automation_domain="content")
    )

    assert result == (first,)


def test_discovery_filters_by_all_requested_tags():
    item = Workflow.create(
        name="Content",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=["create_short_video"],
        discovery_tags=["video", "short-form"],
    )
    item.publish()

    assert DiscoverWorkflows([item]).execute(
        WorkflowDiscoveryQuery(tags=("video", "short-form"))
    ) == (item,)

    assert DiscoverWorkflows([item]).execute(
        WorkflowDiscoveryQuery(tags=("video", "news"))
    ) == ()


def test_workflow_discovery_metadata_is_immutable_exposed_as_tuples():
    item = Workflow.create(
        name="Content",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        automation_domain="content",
        discovery_tags=["video", "short-form"],
    )

    assert item.automation_domain == "content"
    assert item.discovery_tags == ("video", "short-form")


def test_workflow_rejects_duplicate_discovery_tags():
    with pytest.raises(ValueError, match="unique"):
        Workflow.create(
            name="Invalid",
            steps=[WorkflowStep.create(name="Run", capability="run")],
            discovery_tags=["video", "video"],
        )
