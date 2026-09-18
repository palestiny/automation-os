import pytest
from uuid import uuid4

from app.domain.execution import Execution
from app.domain.retry_policy import RetryPolicy


def test_retry_policy_allows_retry_before_max_attempts():
    execution = Execution.create(workflow_id=uuid4())
    policy = RetryPolicy(max_attempts=3)

    execution.start()
    execution.fail()

    assert policy.can_retry(execution) is True


def test_retry_policy_rejects_retry_at_max_attempts():
    execution = Execution.create(workflow_id=uuid4())
    policy = RetryPolicy(max_attempts=3)

    execution.start()
    execution.fail()
    execution.retry()
    execution.start()
    execution.fail()
    execution.retry()
    execution.start()
    execution.fail()

    assert policy.can_retry(execution) is False


def test_retry_policy_requires_positive_max_attempts():
    with pytest.raises(ValueError, match="max_attempts must be at least 1"):
        RetryPolicy(max_attempts=0)
