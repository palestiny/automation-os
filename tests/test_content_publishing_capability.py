import pytest

from app.application.capability import Capability
from app.application.capability_result import CapabilityResult
from app.application.content_publishing import (
    CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY,
    PUBLICATION_CONTEXT_KEY,
    ContentPublishingCapability,
    PublicationProvider,
    PublicationProviderError,
)
from app.application.execution_context import ExecutionContext
from app.domain.content import ContentAsset, Publication, PublicationRequest


class FakePublicationProvider(PublicationProvider):
    def __init__(self, external_reference: str = "provider-ref-123") -> None:
        self.external_reference = external_reference
        self.received_request: PublicationRequest | None = None

    def publish(self, request: PublicationRequest) -> Publication:
        self.received_request = request
        return Publication.create(
            asset=request.asset,
            destination=request.destination,
            external_reference=self.external_reference,
        )


class FailingPublicationProvider(PublicationProvider):
    def publish(self, request: PublicationRequest) -> Publication:
        raise PublicationProviderError("provider rejected publication")


class UnexpectedPublicationProvider(PublicationProvider):
    def publish(self, request: PublicationRequest) -> Publication:
        raise RuntimeError("unexpected provider failure")


def _request() -> PublicationRequest:
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )
    return PublicationRequest.create(
        asset=asset,
        destination="video_platform",
    )


def test_content_publishing_capability_uses_existing_capability_contract():
    capability = ContentPublishingCapability(FakePublicationProvider())

    assert isinstance(capability, Capability)


def test_content_publishing_capability_publishes_request_and_stores_result():
    provider = FakePublicationProvider()
    capability = ContentPublishingCapability(provider)
    context = ExecutionContext()
    request = _request()
    context.set(CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY, request)

    result = capability.execute(context)

    assert isinstance(result, CapabilityResult)
    assert result.succeeded is True
    assert provider.received_request == request

    publication = context.get(PUBLICATION_CONTEXT_KEY)
    assert isinstance(publication, Publication)
    assert publication.asset == request.asset
    assert publication.destination == request.destination
    assert publication.external_reference == "provider-ref-123"


def test_content_publishing_capability_fails_when_request_is_missing():
    capability = ContentPublishingCapability(FakePublicationProvider())

    result = capability.execute(ExecutionContext())

    assert result.succeeded is False
    assert "publication request is required" in str(result.error).lower()


def test_content_publishing_capability_fails_when_request_is_invalid():
    capability = ContentPublishingCapability(FakePublicationProvider())
    context = ExecutionContext()
    context.set(CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY, "not-a-request")

    result = capability.execute(context)

    assert result.succeeded is False
    assert "publication request must be a PublicationRequest instance" in str(
        result.error
    )


def test_content_publishing_capability_translates_expected_provider_failure():
    capability = ContentPublishingCapability(FailingPublicationProvider())
    context = ExecutionContext()
    context.set(CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY, _request())

    result = capability.execute(context)

    assert result.succeeded is False
    assert result.error == "provider rejected publication"
    with pytest.raises(KeyError):
        context.get(PUBLICATION_CONTEXT_KEY)


def test_content_publishing_capability_propagates_unexpected_provider_failure():
    capability = ContentPublishingCapability(UnexpectedPublicationProvider())
    context = ExecutionContext()
    context.set(CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY, _request())

    with pytest.raises(RuntimeError, match="unexpected provider failure"):
        capability.execute(context)

    with pytest.raises(KeyError):
        context.get(PUBLICATION_CONTEXT_KEY)
