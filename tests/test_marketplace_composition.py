from app.application.marketplace_discovery import DiscoverMarketplaceListings
from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.application.marketplace_publication import PublishMarketplaceListing
from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion

def test_marketplace_discovery_to_installation_is_version_pinned():
    workflow=Workflow.create(name="Content",steps=[WorkflowStep.create(name="Run",capability="content_run")],supported_goals=["goal"])
    workflow.publish()
    version=WorkflowVersion.create_from_workflow(workflow,1); version.publish()
    listing=MarketplaceListing.create(workflow.id,version.id,"Create","Create content","content",("goal",),("content",))
    listing=PublishMarketplaceListing([workflow],[version]).execute(listing)
    discovered=DiscoverMarketplaceListings([listing],[workflow],[version]).execute(goal="goal",domain="content")
    installed=InstallMarketplaceWorkflow([workflow],[version]).execute(discovered[0])
    assert discovered==(listing,)
    assert installed is version
