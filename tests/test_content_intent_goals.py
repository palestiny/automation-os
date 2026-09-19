from app.domain.content_intent_goals import CONTENT_INTENT_GOALS


def test_content_intent_goals_are_canonical():
    assert CONTENT_INTENT_GOALS.contains("create_short_video")
    assert CONTENT_INTENT_GOALS.contains("publish_content")


def test_content_intent_goals_do_not_accept_unknown_goals():
    assert not CONTENT_INTENT_GOALS.contains("unknown_goal")
