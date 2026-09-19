from uuid import uuid4

import pytest

from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep


def make_workflow(goals):
    workflow = Workflow.create(
        name="Marketplace workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=list(goals),
    )
    workflow.publish()
    return workflow


def make_listing(workflow, goals=None, visibility=ListingVisibility.PUBLIC):
    return MarketplaceListing.create(
        workflow_id=workflow.id,
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=tuple(goals or workflow.supported_goals),
        tags=("automation",),
        visibility=visibility,
    )


def test_install_returns_existing_published_workflow():
    workflow = make_workflow(("create_short_video",))
    result = InstallMarketplaceWorkflow([workflow]).execute(make_listing(workflow).publish())
    assert result is workflow


def test_install_rejects_unknown_workflow():
    workflow = make_workflow(("create_short_video",))
    listing = make_listing(workflow)
    listing = MarketplaceListing.create(
        workflow_id=uuid4(),
        title=listing.title,
        description=listing.description,
        domain=listing.domain,
        supported_goals=listing.supported_goals,
        tags=listing.tags,
    )
    with pytest.raises(ValueError, match="unknown workflow"):
        InstallMarketplaceWorkflow([workflow]).execute(listing)


def test_install_rejects_draft_workflow():
    workflow = Workflow.create(
        name="Draft",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=["create_short_video"],
    )
    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([workflow]).execute(make_listing(workflow).publish())


def test_install_rejects_unsupported_listing_goal():
    workflow = make_workflow(("create_short_video",))
    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=("publish_content",),
        tags=("automation",),
    )
    with pytest.raises(ValueError, match="supported"):
        InstallMarketplaceWorkflow([workflow]).execute(listing)


def test_install_rejects_hidden_listing():
    workflow = make_workflow(("create_short_video",))
    listing = make_listing(workflow, visibility=ListingVisibility.HIDDEN).publish()
    with pytest.raises(ValueError, match="public"):
        InstallMarketplaceWorkflow([workflow]).execute(listing)


def test_install_does_not_execute_workflow():
    workflow = make_workflow(("create_short_video",))
    result = InstallMarketplaceWorkflow([workflow]).execute(make_listing(workflow).publish())
    assert result.state.name == "PUBLISHED"


def test_install_rejects_draft_listing():
    workflow = make_workflow(("create_short_video",))
    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([workflow]).execute(make_listing(workflow))


def test_install_rejects_withdrawn_listing():
    workflow = make_workflow(("create_short_video",))
    listing = make_listing(workflow).publish().withdraw()
    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([workflow]).execute(listing)
