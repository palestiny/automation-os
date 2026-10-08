from __future__ import annotations

import random
import sys

import pytest

from scripts.benchmark_phase_h_postgres import (
    QueryCounter,
    correctness_passed,
    measure,
    parse_args,
    percentile,
    seeded_uuid,
    summarize,
)


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


def test_measure_repeats_recovery_and_excludes_setup_queries():
    counter = QueryCounter()
    calls = {"setup": 0, "operation": 0}

    def setup():
        calls["setup"] += 1
        counter.statements += 100

    def operation():
        calls["operation"] += 1
        counter.statements += 2

    result = measure(operation, counter, repetitions=3, warmup=1, before_each=setup)

    assert calls == {"setup": 4, "operation": 4}
    assert result["sample_count"] == 3
    assert len(result["latency_samples_ms"]) == 3
    assert result["sql_statement_samples"] == [2, 2, 2]


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



def test_correctness_requires_all_phase_h_invariants():
    correctness = {
        "all_count_matches_seed": True,
        "metrics_count_matches_seed": True,
        "metrics_retry_count_matches_seed": True,
        "recovery_count_matches_seed": True,
    }

    assert correctness_passed(correctness)

    correctness["metrics_retry_count_matches_seed"] = False

    assert not correctness_passed(correctness)


def test_correctness_fails_closed_when_an_invariant_is_missing():
    assert not correctness_passed(
        {
            "all_count_matches_seed": True,
            "metrics_count_matches_seed": True,
            "recovery_count_matches_seed": True,
        }
    )



def test_seeded_uuid_is_repeatable_for_the_same_seed():
    first = random.Random(20261009)
    second = random.Random(20261009)

    assert [seeded_uuid(first) for _ in range(5)] == [
        seeded_uuid(second) for _ in range(5)
    ]


def test_seeded_uuid_changes_when_the_seed_changes():
    first = seeded_uuid(random.Random(1))
    second = seeded_uuid(random.Random(2))

    assert first != second
