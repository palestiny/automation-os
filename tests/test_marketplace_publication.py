from uuid import uuid4

import pytest

from app.application.marketplace_publication import PublishMarketplaceListing
from app.domain.marketplace import ListingStatus, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def make_workflow(goals=("create_short_video",), published=True):
    workflow = Workflow.create(
        name="Marketplace workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=list(goals),
    )
    if published:
        workflow.publish()
    return workflow


def make_version(workflow, published=True):
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    if published:
        version.publish()
    return version


def make_listing(workflow, version, goals=("create_short_video",)):
    return MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=tuple(goals),
        tags=("automation",),
    )


def test_publish_listing_returns_published_listing_for_published_version():
    workflow = make_workflow()
    version = make_version(workflow)
    listing = make_listing(workflow, version)

    result = PublishMarketplaceListing([version]).execute(listing)

    assert result.status == ListingStatus.PUBLISHED


def test_publish_listing_requires_existing_version():
    workflow = make_workflow()
    listing = make_listing(workflow, WorkflowVersion.create_from_workflow(workflow, 1))

    with pytest.raises(ValueError, match="unknown workflow version"):
        PublishMarketplaceListing([]).execute(listing)


def test_publish_listing_requires_published_version():
    workflow = make_workflow()
    version = make_version(workflow, published=False)
    listing = make_listing(workflow, version)

    with pytest.raises(ValueError, match="published"):
        PublishMarketplaceListing([version]).execute(listing)


def test_publish_listing_requires_version_workflow_match():
    workflow = make_workflow()
    other = make_workflow()
    version = make_version(other)
    listing = MarketplaceListing.create(
        workflow.id, version.id, "Listing", "Description", "content",
        ("create_short_video",), ("automation",)
    )

    with pytest.raises(ValueError, match="do not match"):
        PublishMarketplaceListing([version]).execute(listing)


def test_publish_listing_requires_version_support_for_listing_goals():
    workflow = make_workflow(goals=("create_short_video",))
    version = make_version(workflow)
    listing = make_listing(workflow, version, goals=("publish_content",))

    with pytest.raises(ValueError, match="supported"):
        PublishMarketplaceListing([version]).execute(listing)



def test_marketplace_publication_rejects_cross_tenant_workflow_version():
    from app.domain.marketplace import MarketplaceListing
    from app.domain.workflow import Workflow, WorkflowStep
    from app.domain.workflow_version import WorkflowVersion

    tenant_a = uuid4()
    tenant_b = uuid4()
    workflow = Workflow.create(
        "Tenant workflow",
        [WorkflowStep.create("Step", "test")],
    )
    workflow.publish()
    version = WorkflowVersion.create_from_workflow(
        workflow, 1, tenant_id=tenant_a
    )
    version.publish()

    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="Tenant listing",
        description="Description",
        domain="automation",
        supported_goals=("goal",),
        tags=("tag",),
        tenant_id=tenant_b,
    )

    with pytest.raises(ValueError, match="different tenants"):
        PublishMarketplaceListing([version]).execute(listing)
