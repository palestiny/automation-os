from __future__ import annotations

import random
import sys

import pytest

from scripts.benchmark_phase_h_postgres import (
    PHASE_H_SCENARIO_COVERAGE,
    QueryCounter,
    correctness_passed,
    measure,
    parse_args,
    percentile,
    seeded_uuid,
    summarize,
)


def test_p95_requires_at_least_20_samples():
    assert percentile([float(value) for value in range(19)], 0.95) is None
    assert percentile([float(value) for value in range(20)], 0.95) == 18.0


def test_p99_requires_at_least_100_samples():
    assert percentile([float(value) for value in range(99)], 0.99) is None
    assert percentile([float(value) for value in range(100)], 0.99) == 98.0


def test_percentile_uses_ordered_samples_when_sample_size_is_sufficient():
    samples = [float(value) for value in range(20, 0, -1)]
    assert percentile(samples, 0.95) == 19.0


def test_percentile_rejects_fraction_outside_unit_interval():
    with pytest.raises(ValueError, match="fraction must be between 0 and 1"):
        percentile([float(value) for value in range(100)], 1.1)


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
        "state_read_matches_seed": True,
        "history_read_matches_seed": True,
        "history_append_sequence_valid": True,
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
            "state_read_matches_seed": True,
            "history_read_matches_seed": True,
            "history_append_sequence_valid": True,
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

def test_benchmark_rejects_non_postgres_url_scheme(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark_phase_h_postgres.py",
            "--database-url",
            "https://user:secret@localhost/automation_os_bench",
            "--confirm-disposable",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        parse_args()

    assert exc.value.code == 2



def test_scenario_coverage_explicitly_marks_unmeasured_phase_h_workloads():
    assert PHASE_H_SCENARIO_COVERAGE["execution_repository_all"] == "RUN_BY_THIS_HARNESS"
    assert PHASE_H_SCENARIO_COVERAGE["get_execution_metrics"] == "RUN_BY_THIS_HARNESS"
    assert PHASE_H_SCENARIO_COVERAGE["recover_stale_batch_single_run"] == "RUN_BY_THIS_HARNESS"
    assert PHASE_H_SCENARIO_COVERAGE["execution_state_read"] == "RUN_BY_THIS_HARNESS"
    assert PHASE_H_SCENARIO_COVERAGE["history_append_read"] == "RUN_BY_THIS_HARNESS"

    for scenario in (
        "execution_start",

        "idempotent_replay",
        "tenant_isolation",
        "concurrency",
        "throughput",
        "resource_backpressure",
        "load_soak",
    ):
        assert PHASE_H_SCENARIO_COVERAGE[scenario] == "NOT_RUN"


def test_correctness_requires_state_and_history_benchmark_invariants():
    correctness = {
        "all_count_matches_seed": True,
        "metrics_count_matches_seed": True,
        "metrics_retry_count_matches_seed": True,
        "recovery_count_matches_seed": True,
        "state_read_matches_seed": True,
        "history_read_matches_seed": True,
        "history_append_sequence_valid": True,
    }
    assert correctness_passed(correctness)
    correctness["history_append_sequence_valid"] = False
    assert not correctness_passed(correctness)
