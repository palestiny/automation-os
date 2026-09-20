from uuid import uuid4

import pytest

from app.application.marketplace_discovery import DiscoverMarketplaceListings
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def make_artifact(published: bool = True):
    workflow = Workflow.create(
        name="Content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=["create_short_video"],
    )
    workflow.publish()
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    if published:
        version.publish()
    return workflow, version


def make_listing(workflow, version, **kwargs):
    values = {
        "workflow_id": workflow.id,
        "workflow_version_id": version.id,
        "title": "Create content",
        "description": "Create short-form content",
        "domain": "content",
        "supported_goals": ("create_short_video",),
        "tags": ("content",),
    }
    values.update(kwargs)
    return MarketplaceListing.create(**values)


def test_discovery_returns_public_listing_for_published_version():
    workflow, version = make_artifact()
    listing = make_listing(workflow, version).publish()

    assert DiscoverMarketplaceListings([listing], [version]).execute() == (listing,)


def test_discovery_excludes_listing_for_unpublished_version():
    workflow, version = make_artifact(published=False)
    listing = make_listing(workflow, version)

    assert listing.status == ListingStatus.DRAFT
    assert DiscoverMarketplaceListings([listing], [version]).execute() == ()


def test_discovery_excludes_hidden_listing():
    workflow, version = make_artifact()
    listing = make_listing(
        workflow, version, visibility=ListingVisibility.HIDDEN
    ).publish()

    assert DiscoverMarketplaceListings([listing], [version]).execute() == ()


def test_discovery_excludes_missing_version():
    workflow, version = make_artifact()
    listing = make_listing(workflow, version)
    missing = WorkflowVersion.create_from_workflow(workflow, 2)

    assert DiscoverMarketplaceListings([listing], [missing]).execute() == ()


def test_discovery_filters_by_goal_and_domain():
    workflow, version = make_artifact()
    listing = make_listing(workflow, version).publish()
    use_case = DiscoverMarketplaceListings([listing], [version])

    assert use_case.execute(goal="create_short_video") == (listing,)
    assert use_case.execute(goal="publish_content") == ()
    assert use_case.execute(domain="content") == (listing,)
    assert use_case.execute(domain="business") == ()


def test_discovery_search_is_case_insensitive_and_requires_all_terms():
    workflow, version = make_artifact()
    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="Daily Content Automation",
        description="Turn source videos into short clips",
        domain="content",
        supported_goals=("create_short_video",),
        tags=("video", "shorts"),
    ).publish()

    use_case = DiscoverMarketplaceListings([listing], [version])
    assert use_case.execute(search="VIDEO SHORTS") == (listing,)
    assert use_case.execute(search="video finance") == ()


def test_discovery_validates_filters_and_inputs():
    workflow, version = make_artifact()
    listing = make_listing(workflow, version).publish()

    use_case = DiscoverMarketplaceListings([listing], [version])
    with pytest.raises(ValueError):
        use_case.execute(goal="")
    with pytest.raises(ValueError):
        use_case.execute(domain="")
    with pytest.raises(ValueError):
        DiscoverMarketplaceListings([object()], [version])
    with pytest.raises(ValueError):
        DiscoverMarketplaceListings([listing], [object()])
