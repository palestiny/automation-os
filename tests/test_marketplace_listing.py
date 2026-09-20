from uuid import uuid4
import pytest
from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion

def make_workflow(goals=("create_short_video",), published=True):
    workflow=Workflow.create(name="Marketplace workflow",steps=[WorkflowStep.create(name="Run",capability="run")],supported_goals=list(goals))
    version=WorkflowVersion.create_from_workflow(workflow,1)
    if published:
        workflow.publish(); version.publish()
    return workflow,version

def make_listing(workflow,version,goals=None):
    return MarketplaceListing.create(workflow.id,version.id,"Listing","Description","content",tuple(goals or version.supported_goals),("automation",))

def test_listing_has_own_identity_and_pins_exact_version():
    workflow,version=make_workflow()
    listing=make_listing(workflow,version)
    assert listing.id != workflow.id
    assert listing.workflow_id == workflow.id
    assert listing.workflow_version_id == version.id

def test_listing_requires_version_identity():
    with pytest.raises(TypeError):
        MarketplaceListing.create(uuid4(),"Listing","Description","content",("goal",),())
