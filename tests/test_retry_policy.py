from app.application.errors import NetworkTimeoutError
from app.application.retry_policy import RetryPolicy
import pytest


def test_retry_policy_retries_network_timeout():
    policy = RetryPolicy()

    assert policy.should_retry(NetworkTimeoutError()) is True

def test_retry_policy_respects_max_attempts():
    policy = RetryPolicy(max_attempts=3)

    error = NetworkTimeoutError()

    assert policy.should_retry(error, attempt=1) is True
    assert policy.should_retry(error, attempt=2) is True
    assert policy.should_retry(error, attempt=3) is False

def test_retry_policy_rejects_invalid_max_attempts():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)