from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.intent import Intent


@runtime_checkable
class IntentAnalyzer(Protocol):
    """Provider-neutral boundary for converting a raw request into Intent."""

    def analyze(self, request: str) -> Intent:
        ...
