from app.application.marketplace_installation import InstallMarketplaceWorkflow
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import InMemoryWorkflowVersionRepository
import pytest


def make_workflow(goals):
    workflow = Workflow.create(
        name="Marketplace workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=list(goals),
    )
    workflow.publish()
    return workflow


def make_version(workflow, version_number=1):
    version = WorkflowVersion.create_from_workflow(workflow, version_number)
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


def repository_for(*versions):
    repository = InMemoryWorkflowVersionRepository()
    for version in versions:
        repository.save(version)
    return repository


def test_install_returns_exact_published_workflow_version():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    result = InstallMarketplaceWorkflow([workflow], repository_for(version)).execute(
        make_listing(workflow, version).publish()
    )
    assert result is version


def test_install_rejects_unknown_workflow_version():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    missing_version_listing = MarketplaceListing.create(
        workflow_id=workflow.id,
        workflow_version_id=__import__("uuid").uuid4(),
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=version.supported_goals,
        tags=("automation",),
    ).publish()
    with pytest.raises(ValueError, match="unknown WorkflowVersion"):
        InstallMarketplaceWorkflow([workflow], repository_for(version)).execute(
            missing_version_listing
        )


def test_install_rejects_unpublished_workflow_version():
    workflow = make_workflow(("create_short_video",))
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    repository = repository_for(version)
    with pytest.raises(ValueError, match="WorkflowVersion must be published"):
        InstallMarketplaceWorkflow([workflow], repository).execute(
            make_listing(workflow, version).publish()
        )


def test_install_rejects_unsupported_listing_goal():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    listing = make_listing(workflow, version, goals=("publish_content",)).publish()
    with pytest.raises(ValueError, match="supported"):
        InstallMarketplaceWorkflow([workflow], repository_for(version)).execute(listing)


def test_install_rejects_hidden_listing():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    listing = make_listing(workflow, version, visibility=ListingVisibility.HIDDEN).publish()
    with pytest.raises(ValueError, match="public"):
        InstallMarketplaceWorkflow([workflow], repository_for(version)).execute(listing)


def test_install_does_not_execute_workflow():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    result = InstallMarketplaceWorkflow([workflow], repository_for(version)).execute(
        make_listing(workflow, version).publish()
    )
    assert result.state.name == "PUBLISHED"


def test_install_rejects_draft_listing():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([workflow], repository_for(version)).execute(
            make_listing(workflow, version)
        )


def test_install_rejects_withdrawn_listing():
    workflow = make_workflow(("create_short_video",))
    version = make_version(workflow)
    listing = make_listing(workflow, version).publish().withdraw()
    with pytest.raises(ValueError, match="published"):
        InstallMarketplaceWorkflow([workflow], repository_for(version)).execute(listing)


def test_install_rejects_version_from_different_workflow():
    workflow = make_workflow(("create_short_video",))
    other = make_workflow(("create_short_video",))
    version = make_version(other)
    listing = make_listing(workflow, version).publish()
    with pytest.raises(ValueError, match="belong"):
        InstallMarketplaceWorkflow([workflow], repository_for(version)).execute(listing)
