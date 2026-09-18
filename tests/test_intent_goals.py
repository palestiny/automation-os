from app.application.intent_goals import CONTENT_AUTOMATION_GOALS


def test_content_automation_goals_are_canonical():
    assert CONTENT_AUTOMATION_GOALS.goals == (
        "create_short_video",
        "publish_content",
    )
