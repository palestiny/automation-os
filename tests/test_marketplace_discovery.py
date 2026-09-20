from app.application.marketplace_discovery import DiscoverMarketplaceListings
from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow,WorkflowStep
from app.domain.workflow_version import WorkflowVersion

def setup():
    w=Workflow.create(name="Content",steps=[WorkflowStep.create(name="Run",capability="run")],supported_goals=["goal"]); w.publish()
    v=WorkflowVersion.create_from_workflow(w,1); v.publish()
    l=MarketplaceListing.create(w.id,v.id,"Create content","Create short video","content",("goal",),("video","shorts")).publish()
    return w,v,l

def test_discovery_returns_published_version_pinned_listing():
    w,v,l=setup(); assert DiscoverMarketplaceListings([l],[w],[v]).execute()==(l,)

def test_discovery_excludes_listing_when_pinned_version_missing():
    w,v,l=setup(); assert DiscoverMarketplaceListings([l],[w],[]).execute()==()

def test_discovery_search_and_filters_use_version_metadata():
    w,v,l=setup(); assert DiscoverMarketplaceListings([l],[w],[v]).execute(goal="goal",domain="content",search="video shorts")==(l,)
