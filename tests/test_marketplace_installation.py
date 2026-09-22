from uuid import uuid4

import pytest

from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def make_workflow(goals):
    workflow = Workflow.create(
        name="Marketplace workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=list(goals),
    )
    workflow.publish()
    return workflow


def make_version(workflow):
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    return version


def make_listing(workflow, version, goals=None, visibility=ListingVisibility.PUBLIC):
    return MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=tuple(goals or version.supported_goals),
        tags=("automation",),
        visibility=visibility,
    )


def test_install_returns_exact_published_workflow_version():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)

    result = InstallMarketplaceWorkflow([version]).execute(
        make_listing(workflow, version).publish()
    )

    assert result is version


def test_install_rejects_unknown_version():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    listing = make_listing(workflow, version)

    with pytest.raises(ValueError, match="unknown workflow version"):
        InstallMarketplaceWorkflow([]).execute(listing.publish())


def test_install_rejects_unpublished_version():
    workflow = make_workflow(("create_short_video",))
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    listing = make_listing(workflow, version).publish()

    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([version]).execute(listing)


def test_install_rejects_mismatched_workflow_and_version():
    workflow = make_workflow(("create_short_video",))
    other = make_workflow(("create_short_video",))
    version = make_version(other)
    listing = MarketplaceListing.create(
        workflow.id, version.id, "Listing", "Description", "content",
        ("create_short_video",), ("automation",)
    ).publish()

    with pytest.raises(ValueError, match="do not match"):
        InstallMarketplaceWorkflow([version]).execute(listing)



def test_install_rejects_cross_tenant_listing():
    workflow = make_workflow(("create_short_video",))
    version = WorkflowVersion.create_from_workflow(workflow, 1, tenant_id=uuid4())
    version.publish()
    listing = MarketplaceListing.create(
        workflow.id, version.id, "Listing", "Description", "content",
        ("create_short_video",), ("automation",), tenant_id=uuid4()
    ).publish()

    with pytest.raises(ValueError, match="different tenants"):
        InstallMarketplaceWorkflow([version]).execute(listing)


def test_install_version_rejects_cross_tenant_listing():
    from app.application.marketplace_installation import InstallMarketplaceWorkflowVersion

    workflow = make_workflow(("create_short_video",))
    version = WorkflowVersion.create_from_workflow(workflow, 1, tenant_id=uuid4())
    version.publish()
    listing = MarketplaceListing.create(
        workflow.id, version.id, "Listing", "Description", "content",
        ("create_short_video",), ("automation",), tenant_id=uuid4()
    ).publish()

    with pytest.raises(ValueError, match="different tenants"):
        InstallMarketplaceWorkflowVersion([version]).execute(listing)


def test_install_legacy_workflow_listing_preserves_null_tenant_compatibility():
    workflow = make_workflow(("create_short_video",))
    listing = MarketplaceListing.create(
        workflow.id,
        None,
        "Listing",
        "Description",
        "content",
        ("create_short_video",),
        ("automation",),
    ).publish()

    result = InstallMarketplaceWorkflow([workflow]).execute(listing)

    assert result is workflow


def test_install_rejects_unsupported_listing_goal():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    listing = make_listing(workflow, version, goals=("publish_content",)).publish()

    with pytest.raises(ValueError, match="supported"):
        InstallMarketplaceWorkflow([version]).execute(listing)


def test_install_rejects_hidden_listing():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    listing = make_listing(workflow, version, visibility=ListingVisibility.HIDDEN).publish()

    with pytest.raises(ValueError, match="public"):
        InstallMarketplaceWorkflow([version]).execute(listing)


def test_install_does_not_execute_workflow():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)

    result = InstallMarketplaceWorkflow([version]).execute(
        make_listing(workflow, version).publish()
    )

    assert result.state.name == "PUBLISHED"


def test_install_rejects_draft_listing():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)

    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([version]).execute(make_listing(workflow, version))


def test_install_rejects_withdrawn_listing():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    listing = make_listing(workflow, version).publish().withdraw()

    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([version]).execute(listing)
