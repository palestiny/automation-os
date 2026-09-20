from app.application.marketplace_discovery import DiscoverMarketplaceListings
from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.application.marketplace_publication import PublishMarketplaceListing
from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def test_marketplace_discovery_to_installation_returns_exact_version():
    workflow = Workflow.create(
        name="Content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=["create_short_video"],
    )
    workflow.publish()
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()

    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="Create short video",
        description="Create a short-form video",
        domain="content",
        supported_goals=("create_short_video",),
        tags=("content",),
    )

    listing = PublishMarketplaceListing([version]).execute(listing)

    discovered = DiscoverMarketplaceListings([listing], [version]).execute(
        goal="create_short_video",
        domain="content",
    )

    installed = InstallMarketplaceWorkflow([version]).execute(discovered[0])

    assert discovered == (listing,)
    assert installed is version
    assert installed.state.name == "PUBLISHED"
