import pytest
from app.application.marketplace_publication import PublishMarketplaceListing
from app.domain.workflow import Workflow,WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.domain.marketplace import MarketplaceListing

def setup():
    w=Workflow.create(name="Marketplace",steps=[WorkflowStep.create(name="Run",capability="run")],supported_goals=["goal"])
    v=WorkflowVersion.create_from_workflow(w,1); w.publish(); v.publish()
    l=MarketplaceListing.create(w.id,v.id,"Listing","Description","content",("goal",),("automation",))
    return w,v,l

def test_publish_requires_published_exact_version():
    w,v,l=setup(); assert PublishMarketplaceListing([w],[v]).execute(l).status.name=="PUBLISHED"

def test_publish_rejects_unknown_version():
    w,v,l=setup()
    l=MarketplaceListing.create(w.id,WorkflowVersion.create_from_workflow(w,2).id,l.title,l.description,l.domain,l.supported_goals,l.tags)
    with pytest.raises(ValueError,match="unknown workflow version"): PublishMarketplaceListing([w],[v]).execute(l)

def test_publish_rejects_version_from_different_workflow():
    w,v,l=setup()
    other=Workflow.create(name="Other",steps=[WorkflowStep.create(name="Run",capability="run")],supported_goals=["goal"]); other.publish()
    ov=WorkflowVersion.create_from_workflow(other,1); ov.publish()
    bad=MarketplaceListing.create(w.id,ov.id,l.title,l.description,l.domain,l.supported_goals,l.tags)
    with pytest.raises(ValueError,match="do not match"): PublishMarketplaceListing([w],[v,ov]).execute(bad)

def test_publish_rejects_unpublished_version():
    w,v,l=setup(); draft=WorkflowVersion.create_from_workflow(w,2)
    bad=MarketplaceListing.create(w.id,draft.id,l.title,l.description,l.domain,l.supported_goals,l.tags)
    with pytest.raises(ValueError,match="version must be published"): PublishMarketplaceListing([w],[v,draft]).execute(bad)
