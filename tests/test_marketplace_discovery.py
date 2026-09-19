from uuid import uuid4

import pytest

from app.application.marketplace_discovery import DiscoverMarketplaceListings
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep


def make_workflow(published: bool = True) -> Workflow:
    workflow = Workflow.create(
        name="Content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
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


def test_discovery_returns_public_listing_for_published_workflow():
    workflow = make_workflow()
    listing = make_listing(workflow.id).publish()

    result = DiscoverMarketplaceListings([listing], [workflow]).execute()

    assert result == (listing,)


def test_discovery_excludes_hidden_listing():
    workflow = make_workflow()
    listing = make_listing(workflow.id, visibility=ListingVisibility.HIDDEN).publish()

    assert DiscoverMarketplaceListings([listing], [workflow]).execute() == ()


def test_discovery_excludes_listing_for_unpublished_workflow():
    workflow = make_workflow(published=False)
    listing = make_listing(workflow.id)

    assert listing.status == ListingStatus.DRAFT
    assert DiscoverMarketplaceListings([listing], [workflow]).execute() == ()


def test_discovery_excludes_listing_with_missing_workflow():
    listing = make_listing(uuid4()).publish()

    assert DiscoverMarketplaceListings([listing], []).execute() == ()


def test_discovery_filters_by_goal_and_domain():
    workflow = make_workflow()
    listing = make_listing(workflow.id).publish()

    use_case = DiscoverMarketplaceListings([listing], [workflow])

    assert use_case.execute(goal="create_short_video") == (listing,)
    assert use_case.execute(goal="publish_content") == ()
    assert use_case.execute(domain="content") == (listing,)
    assert use_case.execute(domain="business") == ()


def test_discovery_validates_filters():
    workflow = make_workflow()
    listing = make_listing(workflow.id).publish()

    use_case = DiscoverMarketplaceListings([listing], [workflow])

    with pytest.raises(ValueError):
        use_case.execute(goal="")
    with pytest.raises(ValueError):
        use_case.execute(domain="")


def test_discovery_requires_valid_inputs():
    with pytest.raises(ValueError):
        DiscoverMarketplaceListings([object()], [])
    with pytest.raises(ValueError):
        DiscoverMarketplaceListings([], [object()])


def test_search_matches_all_terms_across_listing_metadata():
    workflow = Workflow.create(
        name="content automation",
        steps=[WorkflowStep.create(name="Acquire", capability="acquire")],
        supported_goals=("content.publish",),
    ).publish()
    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        title="Daily Content Automation",
        description="Turn source videos into short clips",
        domain="content",
        supported_goals=("content.publish",),
        tags=("video", "shorts"),
    ).publish()

    discovered = DiscoverMarketplaceListings([listing], [workflow]).execute(
        search="video clips"
    )

    assert discovered == (listing,)


def test_search_requires_every_term_to_match():
    workflow = Workflow.create(
        name="content automation",
        steps=[WorkflowStep.create(name="Acquire", capability="acquire")],
        supported_goals=("content.publish",),
    ).publish()
    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        title="Daily Content Automation",
        description="Turn source videos into short clips",
        domain="content",
        supported_goals=("content.publish",),
        tags=("video", "shorts"),
    ).publish()

    discovered = DiscoverMarketplaceListings([listing], [workflow]).execute(
        search="video finance"
    )

    assert discovered == ()


def test_search_is_case_insensitive():
    workflow = Workflow.create(
        name="content automation",
        steps=[WorkflowStep.create(name="Acquire", capability="acquire")],
        supported_goals=("content.publish",),
    ).publish()
    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        title="Daily Content Automation",
        description="Turn source videos into short clips",
        domain="content",
        supported_goals=("content.publish",),
        tags=("video", "shorts"),
    ).publish()

    discovered = DiscoverMarketplaceListings([listing], [workflow]).execute(
        search="VIDEO SHORTS"
    )

    assert discovered == (listing,)
