from __future__ import annotations

from app.application.intent_goal_catalog import IntentGoalCatalog


CONTENT_INTENT_GOALS = IntentGoalCatalog.create(
    [
        "create_short_video",
        "publish_content",
    ]
)
