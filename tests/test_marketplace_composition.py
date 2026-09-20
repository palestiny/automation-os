from app.application.marketplace_discovery import DiscoverMarketplaceListings
from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.application.marketplace_publication import PublishMarketplaceListing
from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import InMemoryWorkflowVersionRepository


def test_marketplace_discovery_to_installation_returns_existing_version():
    workflow = Workflow.create(
        name="Content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=["create_short_video"],
    )
    workflow.publish()

    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    versions = InMemoryWorkflowVersionRepository()
    versions.save(version)

    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="Create short video",
        description="Create a short-form video",
        domain="content",
        supported_goals=("create_short_video",),
        tags=("content",),
    )

    listing = PublishMarketplaceListing([workflow], versions).execute(listing)

    discovered = DiscoverMarketplaceListings(
        [listing], [workflow], versions
    ).execute(goal="create_short_video", domain="content")

    installed = InstallMarketplaceWorkflow([workflow], versions).execute(discovered[0])

    assert discovered == (listing,)
    assert installed is version
    assert installed.state.name == "PUBLISHED"
