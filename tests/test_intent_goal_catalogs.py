from app.application.intent_goal_catalog import IntentGoalCatalog
from app.infrastructure.intent_goal_catalogs import CONTENT_AUTOMATION_GOALS


def test_content_catalog_contains_only_canonical_content_goals():
    assert CONTENT_AUTOMATION_GOALS.contains("create_short_video")
    assert CONTENT_AUTOMATION_GOALS.contains("publish_content")
    assert not CONTENT_AUTOMATION_GOALS.contains("generate_report")


def test_domain_catalogs_can_be_composed():
    business = IntentGoalCatalog.create(["generate_report"])

    combined = IntentGoalCatalog.combine(CONTENT_AUTOMATION_GOALS, business)

    assert combined.goals == (
        "create_short_video",
        "publish_content",
        "generate_report",
    )


def test_composing_catalogs_rejects_duplicate_goals():
    duplicate = IntentGoalCatalog.create(["publish_content"])

    try:
        IntentGoalCatalog.combine(CONTENT_AUTOMATION_GOALS, duplicate)
    except ValueError as exc:
        assert "publish_content" in str(exc)
    else:
        raise AssertionError("Expected duplicate goal to be rejected")
