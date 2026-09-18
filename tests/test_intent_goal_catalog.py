import pytest

from app.application.intent_goal_catalog import IntentGoalCatalog


def test_goal_catalog_accepts_unique_canonical_goals():
    catalog = IntentGoalCatalog.create(["create_short_video", "publish_content"])

    assert catalog.contains("create_short_video")
    assert catalog.goals == ("create_short_video", "publish_content")


def test_goal_catalog_rejects_empty_goals():
    with pytest.raises(ValueError, match="non-empty"):
        IntentGoalCatalog.create([""])


def test_goal_catalog_rejects_duplicate_goals():
    with pytest.raises(ValueError, match="unique"):
        IntentGoalCatalog.create(["create_short_video", "create_short_video"])


def test_goal_catalog_is_immutable():
    catalog = IntentGoalCatalog.create(["create_short_video"])

    with pytest.raises(AttributeError):
        catalog.goals = ("other",)


def test_unknown_goal_is_not_in_catalog():
    catalog = IntentGoalCatalog.create(["create_short_video"])

    assert not catalog.contains("unknown_goal")
