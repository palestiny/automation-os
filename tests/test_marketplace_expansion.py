from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def make_published_version():
    workflow = Workflow.create(
        name="Marketplace workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=["create_short_video"],
    )
    workflow.publish()
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    return workflow, version


def test_listing_has_stable_identity_and_pins_immutable_workflow_version():
    workflow, version = make_published_version()

    listing = MarketplaceListing.create(
        workflow_version_id=version.id,
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=("create_short_video",),
        tags=("automation",),
    )

    assert listing.id is not None
    assert listing.workflow_version_id == version.id
    assert listing.workflow_id == workflow.id


def test_listing_repository_round_trip_preserves_identity():
    from app.infrastructure.persistence.in_memory import InMemoryMarketplaceListingRepository

    _, version = make_published_version()
    listing = MarketplaceListing.create(
        workflow_version_id=version.id,
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=("create_short_video",),
        tags=("automation",),
    )

    repository = InMemoryMarketplaceListingRepository()
    repository.save(listing)

    assert repository.get(listing.id) == listing
    assert repository.all() == (listing,)


def test_installation_is_version_pinned():
    from app.application.marketplace_installation import InstallMarketplaceWorkflowVersion

    _, version = make_published_version()
    later = WorkflowVersion.create_from_version(version, 2)
    later.publish()

    listing = MarketplaceListing.create(
        workflow_version_id=version.id,
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=("create_short_video",),
        tags=("automation",),
    ).publish()

    installed = InstallMarketplaceWorkflowVersion([version, later]).execute(listing)

    assert installed.id == version.id
    assert installed.id != later.id
