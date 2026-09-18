from __future__ import annotations

from app.application.intent_goal_catalog import IntentGoalCatalog
from app.domain.intent import Intent


class ValidateIntent:
    """Validates analyzed Intent values against canonical platform goals."""

    def __init__(self, goal_catalog: IntentGoalCatalog) -> None:
        if not isinstance(goal_catalog, IntentGoalCatalog):
            raise TypeError("goal_catalog must be an IntentGoalCatalog instance")
        self._goal_catalog = goal_catalog

    def execute(self, intent: Intent) -> Intent:
        if not isinstance(intent, Intent):
            raise TypeError("intent must be an Intent instance")
        if not self._goal_catalog.contains(intent.goal):
            raise ValueError("Intent goal is not supported by the platform")
        return intent
