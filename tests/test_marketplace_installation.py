from uuid import uuid4

import pytest

from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.domain.marketplace import ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep


def make_workflow(published=True):
    workflow = Workflow.create(
        name="Content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=["create_short_video"],
    )
    if published:
        workflow.publish()
    return workflow


def make_listing(workflow_id, **kwargs):
    values = {
        "workflow_id": workflow_id,
        "title": "Create content",
        "description": "Create short-form content",
        "domain": "content",
        "supported_goals": ("create_short_video",),
        "tags": ("content",),
    }
    values.update(kwargs)
    return MarketplaceListing.create(**values)


def test_installation_returns_existing_published_workflow():
    workflow = make_workflow()
    listing = make_listing(workflow.id)

    installed = InstallMarketplaceWorkflow([workflow]).execute(listing)

    assert installed is workflow


def test_installation_rejects_hidden_listing():
    workflow = make_workflow()
    listing = make_listing(workflow.id, visibility=ListingVisibility.HIDDEN)

    with pytest.raises(ValueError, match="public"):
        InstallMarketplaceWorkflow([workflow]).execute(listing)


def test_installation_rejects_unpublished_workflow():
    workflow = make_workflow(published=False)
    listing = make_listing(workflow.id)

    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([workflow]).execute(listing)


def test_installation_rejects_missing_workflow_reference():
    listing = make_listing(uuid4())

    with pytest.raises(ValueError, match="workflow"):
        InstallMarketplaceWorkflow([]).execute(listing)


def test_installation_rejects_listing_goal_not_supported_by_workflow():
    workflow = make_workflow()
    listing = make_listing(workflow.id, supported_goals=("publish_content",))

    with pytest.raises(ValueError, match="goal"):
        InstallMarketplaceWorkflow([workflow]).execute(listing)


def test_installation_requires_listing():
    with pytest.raises(TypeError):
        InstallMarketplaceWorkflow([]).execute(None)
