from uuid import uuid4

import pytest

from app.application.marketplace_publication import PublishMarketplaceListing
from app.domain.marketplace import ListingStatus, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep


def make_workflow(goals=("create_short_video",), published=True):
    workflow = Workflow.create(
        name="Marketplace workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=list(goals),
    )
    if published:
        workflow.publish()
    return workflow


def make_listing(workflow_id, goals=("create_short_video",)):
    return MarketplaceListing.create(
        workflow_id=workflow_id,
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=tuple(goals),
        tags=("automation",),
    )


def test_publish_listing_returns_published_listing_for_published_workflow():
    workflow = make_workflow()
    listing = make_listing(workflow.id)

    result = PublishMarketplaceListing([workflow]).execute(listing)

    assert result.status == ListingStatus.PUBLISHED


def test_publish_listing_requires_existing_workflow():
    listing = make_listing(uuid4())

    with pytest.raises(ValueError, match="unknown workflow"):
        PublishMarketplaceListing([]).execute(listing)


def test_publish_listing_requires_published_workflow():
    workflow = make_workflow(published=False)
    listing = make_listing(workflow.id)

    with pytest.raises(ValueError, match="published"):
        PublishMarketplaceListing([workflow]).execute(listing)


def test_publish_listing_requires_workflow_support_for_listing_goals():
    workflow = make_workflow(goals=("create_short_video",))
    listing = make_listing(workflow.id, goals=("publish_content",))

    with pytest.raises(ValueError, match="supported"):
        PublishMarketplaceListing([workflow]).execute(listing)


def test_publish_listing_does_not_execute_workflow():
    workflow = make_workflow()
    listing = make_listing(workflow.id)

    result = PublishMarketplaceListing([workflow]).execute(listing)

    assert result.status == ListingStatus.PUBLISHED
    assert workflow.state.name == "PUBLISHED"
