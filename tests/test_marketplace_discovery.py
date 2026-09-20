from app.application.marketplace_discovery import DiscoverMarketplaceListings
from app.domain.marketplace import ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def make_workflow(goals=("create_short_video",)):
    workflow = Workflow.create(
        name="Marketplace workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=list(goals),
    )
    workflow.publish()
    return workflow


def make_version(workflow, published=True):
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    if published:
        version.publish()
    return version


def make_listing(workflow, version, **kwargs):
    return MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title=kwargs.get("title", "Listing"),
        description=kwargs.get("description", "Description"),
        domain=kwargs.get("domain", "content"),
        supported_goals=tuple(kwargs.get("goals", version.supported_goals)),
        tags=tuple(kwargs.get("tags", ("automation",))),
        visibility=kwargs.get("visibility", ListingVisibility.PUBLIC),
        status=kwargs.get("status", MarketplaceListing.create(
            workflow.id, version.id, "x", "x", "x", ("x",), ()
        ).status),
    )


def published_listing(workflow, version, **kwargs):
    return make_listing(workflow, version, **kwargs).publish()


def test_discovery_returns_only_public_published_version_backed_listings():
    workflow = make_workflow()
    version = make_version(workflow)
    visible = published_listing(workflow, version)

    draft = make_listing(workflow, version)
    hidden = published_listing(workflow, version, visibility=ListingVisibility.HIDDEN)

    assert DiscoverMarketplaceListings(
        [visible, draft, hidden],
        [version],
    ).execute() == (visible,)


def test_discovery_rejects_unpublished_version_backing():
    workflow = make_workflow()
    version = make_version(workflow, published=False)
    listing = published_listing(workflow, version)

    assert DiscoverMarketplaceListings([listing], [version]).execute() == ()


def test_discovery_filters_goal_domain_and_search_terms():
    workflow = make_workflow()
    version = make_version(workflow)
    listing = published_listing(
        workflow,
        version,
        domain="video",
        title="Video automation",
        description="Create a short video",
        goals=("create_short_video",),
        tags=("video", "automation"),
    )

    service = DiscoverMarketplaceListings([listing], [version])

    assert service.execute(goal="create_short_video") == (listing,)
    assert service.execute(domain="video") == (listing,)
    assert service.execute(search="video automation") == (listing,)
    assert service.execute(search="missing") == ()


def test_discovery_rejects_listing_version_mismatch():
    workflow = make_workflow()
    other = make_workflow()
    version = make_version(other)
    listing = published_listing(workflow, version)

    assert DiscoverMarketplaceListings([listing], [version]).execute() == ()
