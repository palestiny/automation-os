from app.application.intent_goals import CONTENT_AUTOMATION_GOALS


def test_content_automation_goals_are_canonical():
    assert CONTENT_AUTOMATION_GOALS.goals == (
        "create_short_video",
        "publish_content",
    )


def test_content_automation_goal_catalog_contains_known_goals():
    assert CONTENT_AUTOMATION_GOALS.contains("create_short_video")
    assert CONTENT_AUTOMATION_GOALS.contains("publish_content")
