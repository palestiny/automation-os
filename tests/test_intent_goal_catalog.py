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


def test_goal_catalog_can_combine_independent_domain_catalogs():
    content = IntentGoalCatalog.create(["create_short_video", "publish_content"])
    business = IntentGoalCatalog.create(["generate_report", "send_report"])

    combined = IntentGoalCatalog.combine(content, business)

    assert combined.goals == (
        "create_short_video",
        "publish_content",
        "generate_report",
        "send_report",
    )


def test_goal_catalog_rejects_duplicate_across_domains():
    content = IntentGoalCatalog.create(["publish_content"])
    business = IntentGoalCatalog.create(["publish_content"])

    with pytest.raises(ValueError, match="Duplicate intent goal"):
        IntentGoalCatalog.combine(content, business)


def test_goal_catalog_requires_catalog_instances_when_combining():
    with pytest.raises(TypeError):
        IntentGoalCatalog.combine(IntentGoalCatalog.create(["goal"]), object())
