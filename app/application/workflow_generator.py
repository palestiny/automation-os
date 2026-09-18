from __future__ import annotations

from typing import Protocol

from app.application.workflow_generation import WorkflowCandidate
from app.domain.intent import Intent


class WorkflowGenerator(Protocol):
    """Application boundary for proposing a provider-neutral workflow candidate."""

    def generate(self, intent: Intent) -> WorkflowCandidate: ...
