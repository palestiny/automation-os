from uuid import uuid4

import pytest

from app.application.marketplace_discovery import DiscoverMarketplaceListings
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import InMemoryWorkflowVersionRepository


def make_workflow(published: bool = True) -> Workflow:
    workflow = Workflow.create(
        name="Content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=("create_short_video",),
    )
    if published:
        workflow.publish()
    return workflow


def make_version(workflow, version_number=1, published=True):
    version = WorkflowVersion.create_from_workflow(workflow, version_number)
    if published:
        version.publish()
    return version


def make_listing(workflow, version=None, **kwargs):
    values = {
        "workflow_id": workflow.id,
        "workflow_version_id": version.id if version is not None else None,
        "title": "Create content",
        "description": "Create short-form content",
        "domain": "content",
        "supported_goals": ("create_short_video",),
        "tags": ("content",),
    }
    values.update(kwargs)
    return MarketplaceListing.create(**values)


def repository_for(*versions):
    repository = InMemoryWorkflowVersionRepository()
    for version in versions:
        repository.save(version)
    return repository


def test_discovery_returns_public_listing_for_published_version():
    workflow = make_workflow()
    version = make_version(workflow)
    listing = make_listing(workflow, version).publish()

    result = DiscoverMarketplaceListings(
        [listing], [workflow], repository_for(version)
    ).execute()

    assert result == (listing,)


def test_discovery_excludes_hidden_listing():
    workflow = make_workflow()
    version = make_version(workflow)
    listing = make_listing(
        workflow, version, visibility=ListingVisibility.HIDDEN
    ).publish()

    assert DiscoverMarketplaceListings(
        [listing], [workflow], repository_for(version)
    ).execute() == ()


def test_discovery_excludes_listing_for_unpublished_version():
    workflow = make_workflow()
    version = make_version(workflow, published=False)
    repository = repository_for(version)
    listing = make_listing(workflow, version)

    # Legacy/draft listing is never discoverable.
    assert listing.status == ListingStatus.DRAFT
    assert DiscoverMarketplaceListings(
        [listing], [workflow], repository
    ).execute() == ()


def test_discovery_excludes_listing_with_missing_workflow():
    workflow = make_workflow()
    version = make_version(workflow)
    listing = make_listing(workflow, version).publish()

    assert DiscoverMarketplaceListings(
        [listing], [], repository_for(version)
    ).execute() == ()


def test_discovery_excludes_legacy_unversioned_listing():
    workflow = make_workflow()
    listing = make_listing(workflow).publish()

    assert DiscoverMarketplaceListings(
        [listing], [workflow], InMemoryWorkflowVersionRepository()
    ).execute() == ()


def test_discovery_filters_by_goal_and_domain():
    workflow = make_workflow()
    version = make_version(workflow)
    listing = make_listing(workflow, version).publish()

    use_case = DiscoverMarketplaceListings(
        [listing], [workflow], repository_for(version)
    )

    assert use_case.execute(goal="create_short_video") == (listing,)
    assert use_case.execute(goal="publish_content") == ()
    assert use_case.execute(domain="content") == (listing,)
    assert use_case.execute(domain="business") == ()


def test_discovery_validates_filters():
    workflow = make_workflow()
    version = make_version(workflow)
    listing = make_listing(workflow, version).publish()

    use_case = DiscoverMarketplaceListings(
        [listing], [workflow], repository_for(version)
    )

    with pytest.raises(ValueError):
        use_case.execute(goal="")
    with pytest.raises(ValueError):
        use_case.execute(domain="")


def test_discovery_requires_valid_inputs():
    with pytest.raises(ValueError):
        DiscoverMarketplaceListings([object()], [], InMemoryWorkflowVersionRepository())
    with pytest.raises(ValueError):
        DiscoverMarketplaceListings([], [object()], InMemoryWorkflowVersionRepository())


def test_search_matches_all_terms_across_listing_metadata():
    workflow = Workflow.create(
        name="content automation",
        steps=[WorkflowStep.create(name="Acquire", capability="acquire")],
        supported_goals=("content.publish",),
    )
    workflow.publish()
    version = make_version(workflow)
    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="Daily Content Automation",
        description="Turn source videos into short clips",
        domain="content",
        supported_goals=("content.publish",),
        tags=("video", "shorts"),
    ).publish()

    discovered = DiscoverMarketplaceListings(
        [listing], [workflow], repository_for(version)
    ).execute(search="video clips")

    assert discovered == (listing,)


def test_search_requires_every_term_to_match():
    workflow = Workflow.create(
        name="content automation",
        steps=[WorkflowStep.create(name="Acquire", capability="acquire")],
        supported_goals=("content.publish",),
    )
    workflow.publish()
    version = make_version(workflow)
    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="Daily Content Automation",
        description="Turn source videos into short clips",
        domain="content",
        supported_goals=("content.publish",),
        tags=("video", "shorts"),
    ).publish()

    discovered = DiscoverMarketplaceListings(
        [listing], [workflow], repository_for(version)
    ).execute(search="video finance")

    assert discovered == ()


def test_search_is_case_insensitive():
    workflow = Workflow.create(
        name="content automation",
        steps=[WorkflowStep.create(name="Acquire", capability="acquire")],
        supported_goals=("content.publish",),
    )
    workflow.publish()
    version = make_version(workflow)
    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="Daily Content Automation",
        description="Turn source videos into short clips",
        domain="content",
        supported_goals=("content.publish",),
        tags=("video", "shorts"),
    ).publish()

    discovered = DiscoverMarketplaceListings(
        [listing], [workflow], repository_for(version)
    ).execute(search="VIDEO SHORTS")

    assert discovered == (listing,)


def test_new_workflow_version_does_not_change_existing_listing():
    workflow = make_workflow()
    version_one = make_version(workflow, 1)
    listing = make_listing(workflow, version_one).publish()

    version_two = make_version(workflow, 2)
    repository = repository_for(version_one, version_two)

    discovered = DiscoverMarketplaceListings(
        [listing], [workflow], repository
    ).execute()

    assert discovered == (listing,)
    assert listing.workflow_version_id == version_one.id
