from __future__ import annotations

import sys

import pytest

from scripts.benchmark_phase_h_postgres import parse_args, percentile, summarize


def test_percentiles_are_not_reported_for_small_samples():
    assert percentile([0.1, 0.2, 0.3, 0.4, 0.5], 0.95) is None


def test_percentile_uses_ordered_samples_when_sample_size_is_sufficient():
    samples = [float(value) for value in range(20, 0, -1)]
    assert percentile(samples, 0.95) == 19.0


def test_summary_reports_latency_and_query_count_statistics():
    result = summarize([0.01, 0.03, 0.02], [4, 6, 5])

    assert result["sample_count"] == 3
    assert result["median_ms"] == 20.0
    assert result["p95_ms"] is None
    assert result["p99_ms"] is None
    assert result["sql_statements_median"] == 5


def test_benchmark_refuses_production_like_database_name(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark_phase_h_postgres.py",
            "--database-url",
            "postgresql://user:secret@localhost/production_db",
            "--confirm-disposable",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        parse_args()

    assert exc.value.code == 2


def test_benchmark_requires_disposable_acknowledgement(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark_phase_h_postgres.py",
            "--database-url",
            "postgresql://user:secret@localhost/automation_os_bench",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        parse_args()

    assert exc.value.code == 2
