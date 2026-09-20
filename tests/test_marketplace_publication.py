from uuid import uuid4

import pytest

from app.application.marketplace_publication import PublishMarketplaceListing
from app.domain.marketplace import ListingStatus, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import InMemoryWorkflowVersionRepository


def make_workflow(goals=("create_short_video",), published=True):
    workflow = Workflow.create(
        name="Marketplace workflow",
        steps=[WorkflowStep.create(name="Run", capability="run")],
        supported_goals=list(goals),
    )
    if published:
        workflow.publish()
    return workflow


def make_version(workflow):
    version = __import__("app.domain.workflow_version", fromlist=["WorkflowVersion"]).WorkflowVersion.create_from_workflow(
        workflow, 1
    )
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


def test_publish_listing_returns_published_listing_for_published_workflow_version():
    workflow = make_workflow()
    version = make_version(workflow)
    repository = InMemoryWorkflowVersionRepository()
    repository.save(version)

    result = PublishMarketplaceListing([workflow], repository).execute(
        make_listing(workflow, version)
    )

    assert result.status == ListingStatus.PUBLISHED
    assert result.workflow_version_id == version.id


def test_publish_listing_requires_existing_workflow():
    workflow = make_workflow()
    version = make_version(workflow)
    repository = InMemoryWorkflowVersionRepository()
    repository.save(version)

    listing = make_listing(workflow, version)
    with pytest.raises(ValueError, match="unknown workflow"):
        PublishMarketplaceListing([], repository).execute(listing)


def test_publish_listing_requires_published_workflow_version():
    workflow = make_workflow()
    version = __import__("app.domain.workflow_version", fromlist=["WorkflowVersion"]).WorkflowVersion.create_from_workflow(
        workflow, 1
    )
    repository = InMemoryWorkflowVersionRepository()
    repository.save(version)

    with pytest.raises(ValueError, match="WorkflowVersion must be published"):
        PublishMarketplaceListing([workflow], repository).execute(
            make_listing(workflow, version)
        )


def test_publish_listing_requires_version_pin():
    workflow = make_workflow()
    repository = InMemoryWorkflowVersionRepository()
    with pytest.raises(ValueError, match="must pin"):
        PublishMarketplaceListing([workflow], repository).execute(
            MarketplaceListing.create(
                workflow.id, "Listing", "Description", "content",
                ("create_short_video",), ()
            )
        )


def test_publish_listing_requires_workflow_support_for_listing_goals():
    workflow = make_workflow(goals=("create_short_video",))
    version = make_version(workflow)
    repository = InMemoryWorkflowVersionRepository()
    repository.save(version)

    with pytest.raises(ValueError, match="supported"):
        PublishMarketplaceListing([workflow], repository).execute(
            make_listing(workflow, version, goals=("publish_content",))
        )


def test_publish_listing_rejects_version_from_different_workflow():
    workflow = make_workflow()
    other = make_workflow()
    version = make_version(other)
    repository = InMemoryWorkflowVersionRepository()
    repository.save(version)

    with pytest.raises(ValueError, match="belong"):
        PublishMarketplaceListing([workflow], repository).execute(
            make_listing(workflow, version)
        )


def test_publish_listing_does_not_execute_workflow():
    workflow = make_workflow()
    version = make_version(workflow)
    repository = InMemoryWorkflowVersionRepository()
    repository.save(version)

    result = PublishMarketplaceListing([workflow], repository).execute(
        make_listing(workflow, version)
    )

    assert result.status == ListingStatus.PUBLISHED
    assert workflow.state.name == "PUBLISHED"
