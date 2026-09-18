import pytest

from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.intent_validation import ValidateIntent
from app.domain.intent import Intent


def test_validate_intent_accepts_canonical_goal():
    validator = ValidateIntent(IntentGoalCatalog.create(["create_short_video"]))
    intent = Intent.create("create_short_video", {"source": "youtube"})

    assert validator.execute(intent) is intent


def test_validate_intent_rejects_unknown_goal():
    validator = ValidateIntent(IntentGoalCatalog.create(["create_short_video"]))

    with pytest.raises(ValueError, match="not supported"):
        validator.execute(Intent.create("unknown_goal"))


def test_validate_intent_requires_intent():
    validator = ValidateIntent(IntentGoalCatalog.create(["create_short_video"]))

    with pytest.raises(TypeError):
        validator.execute(object())


def test_validate_intent_requires_catalog():
    with pytest.raises(TypeError):
        ValidateIntent(None)
