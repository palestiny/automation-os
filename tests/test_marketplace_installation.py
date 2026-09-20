from uuid import uuid4

import pytest

from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


def make_artifact(goals=("create_short_video",), published=True):
    workflow = Workflow.create(
        name="Marketplace workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=list(goals),
    )
    workflow.publish()
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    if published:
        version.publish()
    return workflow, version


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


def test_install_returns_exact_published_version():
    workflow, version = make_artifact()
    result = InstallMarketplaceWorkflow([version]).execute(
        make_listing(workflow, version).publish()
    )
    assert result is version


def test_install_rejects_unknown_version():
    workflow, version = make_artifact()
    listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=uuid4(),
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=version.supported_goals,
        tags=("automation",),
    ).publish()

    with pytest.raises(ValueError, match="unknown workflow version"):
        InstallMarketplaceWorkflow([version]).execute(listing)


def test_install_rejects_unpublished_version():
    workflow, version = make_artifact(published=False)

    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([version]).execute(
            make_listing(workflow, version).publish()
        )


def test_install_rejects_unsupported_listing_goal():
    workflow, version = make_artifact()
    listing = make_listing(
        workflow, version, goals=("publish_content",)
    ).publish()

    with pytest.raises(ValueError, match="supported"):
        InstallMarketplaceWorkflow([version]).execute(listing)


def test_install_rejects_hidden_listing():
    workflow, version = make_artifact()
    listing = make_listing(
        workflow, version, visibility=ListingVisibility.HIDDEN
    ).publish()

    with pytest.raises(ValueError, match="public"):
        InstallMarketplaceWorkflow([version]).execute(listing)


def test_install_does_not_execute_workflow():
    workflow, version = make_artifact()
    result = InstallMarketplaceWorkflow([version]).execute(
        make_listing(workflow, version).publish()
    )
    assert result is version


def test_install_rejects_draft_listing():
    workflow, version = make_artifact()

    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([version]).execute(
            make_listing(workflow, version)
        )


def test_install_rejects_withdrawn_listing():
    workflow, version = make_artifact()
    listing = make_listing(workflow, version).publish().withdraw()

    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([version]).execute(listing)
