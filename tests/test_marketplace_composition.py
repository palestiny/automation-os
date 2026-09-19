from app.application.marketplace_discovery import DiscoverMarketplaceListings
from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep


def test_marketplace_discovery_to_installation_returns_existing_workflow():
    workflow = Workflow.create(
        name="Content workflow",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=["create_short_video"],
    )
    workflow.publish()

    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        title="Create short video",
        description="Create a short-form video",
        domain="content",
        supported_goals=("create_short_video",),
        tags=("content",),
    )

    listing = listing.publish()

    discovered = DiscoverMarketplaceListings([listing], [workflow]).execute(
        goal="create_short_video",
        domain="content",
    )

    installed = InstallMarketplaceWorkflow([workflow]).execute(discovered[0])

    assert discovered == (listing,)
    assert installed is workflow
    assert installed.state.name == "PUBLISHED"
