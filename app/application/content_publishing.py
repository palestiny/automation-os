from __future__ import annotations

from typing import Protocol

from app.application.capability import Capability
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext
from app.domain.content import Publication, PublicationRequest


CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY = "content.publication_request"
PUBLICATION_CONTEXT_KEY = "content.publication"


class PublicationProviderError(Exception):
    """Expected provider-level publication failure."""


class PublicationProvider(Protocol):
    """Provider-neutral technical boundary for content publication."""

    def publish(self, request: PublicationRequest) -> Publication:
        ...


class ContentPublishingCapability(Capability):
    """Publish content through an injected provider adapter."""

    def __init__(self, provider: PublicationProvider) -> None:
        self._provider = provider

    def execute(self, context: ExecutionContext) -> CapabilityResult:
        try:
            request = context.get(CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY)
        except KeyError:
            return CapabilityResult.failure(
                "Publication request is required for publishing"
            )

        if not isinstance(request, PublicationRequest):
            return CapabilityResult.failure(
                "Publication request must be a PublicationRequest instance"
            )

        try:
            publication = self._provider.publish(request)
        except PublicationProviderError as exc:
            return CapabilityResult.failure(str(exc))

        context.set(PUBLICATION_CONTEXT_KEY, publication)
        return CapabilityResult.success()
