from __future__ import annotations

import pytest

from app.application.operational_metrics import (
    NoopOperationalMetrics,
    TimingMetric,
)


def test_timing_metric_rejects_empty_name():
    with pytest.raises(ValueError, match="Metric name cannot be empty"):
        TimingMetric(name="", duration_ms=1)


def test_timing_metric_rejects_negative_duration():
    with pytest.raises(ValueError, match="Metric duration cannot be negative"):
        TimingMetric(name="capability.execution", duration_ms=-1)


def test_timing_metric_accepts_safe_provider_neutral_evidence():
    metric = TimingMetric(
        name="capability.execution",
        duration_ms=12.5,
        outcome="succeeded",
    )

    assert metric.name == "capability.execution"
    assert metric.duration_ms == 12.5
    assert metric.outcome == "succeeded"


def test_noop_metrics_are_safe_default():
    NoopOperationalMetrics().record_timing(
        "capability.execution",
        1.0,
        outcome="succeeded",
    )
