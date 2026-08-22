from app.application.capability_result import CapabilityResult


def test_capability_result_can_represent_success():
    result = CapabilityResult.success()

    assert result.succeeded is True

def test_capability_result_can_represent_failure():
    result = CapabilityResult.failure("Network timeout")

    assert result.succeeded is False
    assert result.error == "Network timeout"

class NetworkTimeoutError(Exception):
    pass


def test_capability_result_can_contain_error():
    error = NetworkTimeoutError()

    result = CapabilityResult.failure(error)

    assert result.succeeded is False
    assert result.error is error