from app.application.intent_goal_catalog import IntentGoalCatalog


CONTENT_AUTOMATION_GOALS = IntentGoalCatalog.create(
    [
        "create_short_video",
        "publish_content",
    ]
)
