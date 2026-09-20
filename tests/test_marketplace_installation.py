import pytest
from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow,WorkflowStep
from app.domain.workflow_version import WorkflowVersion

def setup():
    w=Workflow.create(name="Marketplace",steps=[WorkflowStep.create(name="Run",capability="run")],supported_goals=["goal"]); w.publish()
    v=WorkflowVersion.create_from_workflow(w,1); v.publish()
    l=MarketplaceListing.create(w.id,v.id,"Listing","Description","content",("goal",),("automation",)).publish()
    return w,v,l

def test_install_returns_exact_published_version():
    w,v,l=setup()
    assert InstallMarketplaceWorkflow([w],[v]).execute(l) is v

def test_install_is_pinned_when_newer_version_exists():
    w,v1,l=setup()
    v2=WorkflowVersion.create_from_version(v1,2); v2.publish()
    assert InstallMarketplaceWorkflow([w],[v1,v2]).execute(l) is v1

def test_install_rejects_withdrawn_listing():
    w,v,l=setup(); l=l.withdraw()
    with pytest.raises(ValueError,match="published"): InstallMarketplaceWorkflow([w],[v]).execute(l)
