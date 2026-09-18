from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.intent import Intent


class IntentAnalysisStatus(Enum):
    ANALYZED = "analyzed"
    FAILED = "failed"


@dataclass(frozen=True)
class IntentAnalysisResult:
    status: IntentAnalysisStatus
    intent: Intent | None = None
    error: str | None = None

    @classmethod
    def analyzed(cls, intent: Intent) -> "IntentAnalysisResult":
        if not isinstance(intent, Intent):
            raise TypeError("intent must be an Intent instance")
        return cls(IntentAnalysisStatus.ANALYZED, intent=intent)

    @classmethod
    def failed(cls, error: str) -> "IntentAnalysisResult":
        if not isinstance(error, str) or not error.strip():
            raise ValueError("error must be a non-empty string")
        return cls(IntentAnalysisStatus.FAILED, error=error.strip())
