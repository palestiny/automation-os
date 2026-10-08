from __future__ import annotations

import argparse
import json
import os
import platform
import random
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.execution_metrics import GetExecutionMetrics
from app.application.execution_recovery import (
    ExecutionRecoveryPolicy,
    RecoverStaleExecution,
    RecoverStaleExecutions,
)
from app.domain.execution import ExecutionState
from app.infrastructure.persistence.migrations import PostgresMigrationRunner
from app.infrastructure.persistence.postgres import (
    PostgresExecutionHistoryRepository,
    PostgresExecutionRepository,
)


class CountingCursor:
    def __init__(self, cursor: Any, counter: "QueryCounter") -> None:
        self._cursor = cursor
        self._counter = counter

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        self._counter.statements += 1
        return self._cursor.execute(*args, **kwargs)

    def executemany(self, *args: Any, **kwargs: Any) -> Any:
        self._counter.statements += 1
        return self._cursor.executemany(*args, **kwargs)

    def __enter__(self) -> "CountingCursor":
        self._cursor.__enter__()
        return self

    def __exit__(self, *args: Any) -> Any:
        return self._cursor.__exit__(*args)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)


class CountingConnection:
    def __init__(self, connection: psycopg.Connection[Any], counter: "QueryCounter") -> None:
        self._connection = connection
        self._counter = counter

    def cursor(self, *args: Any, **kwargs: Any) -> CountingCursor:
        return CountingCursor(self._connection.cursor(*args, **kwargs), self._counter)

    def __enter__(self) -> "CountingConnection":
        self._connection.__enter__()
        return self

    def __exit__(self, *args: Any) -> Any:
        return self._connection.__exit__(*args)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)


@dataclass
class QueryCounter:
    statements: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run isolated PostgreSQL baseline characterization for Automation OS."
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("AUTOMATION_OS_BENCHMARK_DATABASE_URL"),
        help="Disposable PostgreSQL DSN. May also be set via AUTOMATION_OS_BENCHMARK_DATABASE_URL.",
    )
    parser.add_argument(
        "--confirm-disposable",
        action="store_true",
        help="Required acknowledgement that the target database is disposable. The harness creates and drops only its own random schema.",
    )
    parser.add_argument(
        "--allow-nonlocal-host",
        action="store_true",
        help="Allow a non-local PostgreSQL hostname after reviewing the target. Production-like database names are always rejected.",
    )
    parser.add_argument("--sizes", type=int, nargs="+", default=[100, 1000])
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--history-events", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261009, help="Deterministic synthetic dataset seed.")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    if not args.database_url:
        parser.error("--database-url or AUTOMATION_OS_BENCHMARK_DATABASE_URL is required")
    if not args.confirm_disposable:
        parser.error("--confirm-disposable is required; never run against a shared or production database")
    if args.repetitions < 1 or args.repetitions > 1000:
        parser.error("--repetitions must be between 1 and 1000")
    if args.warmup < 0 or args.warmup > 100:
        parser.error("--warmup must be between 0 and 100")
    if not args.sizes or any(size < 1 or size > 100_000 for size in args.sizes):
        parser.error("--sizes must contain values between 1 and 100000")
    if args.history_events < 1 or args.history_events > 100:
        parser.error("--history-events must be between 1 and 100")
    if len(set(args.sizes)) != len(args.sizes):
        parser.error("--sizes must not contain duplicates")
    if any(size * args.history_events > 100_000 for size in args.sizes):
        parser.error("each dataset may seed at most 100000 history rows; reduce --sizes or --history-events")

    parsed = urlparse(args.database_url)
    host = (parsed.hostname or "").lower()
    database = parsed.path.lstrip("/").lower()
    if not host or not database:
        parser.error("database URL must include a hostname and database name")
    if any(word in database for word in ("prod", "production", "live")):
        parser.error("refusing a production-like database name")
    if host not in {"localhost", "127.0.0.1", "::1", "postgres"} and not args.allow_nonlocal_host:
        parser.error("non-local host refused; inspect the target and pass --allow-nonlocal-host only for a disposable environment")

    return args


def percentile(samples: list[float], fraction: float) -> float | None:
    if len(samples) < 20:
        return None
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * fraction)))
    return ordered[index]


def summarize(samples: list[float], query_counts: list[int]) -> dict[str, Any]:
    return {
        "sample_count": len(samples),
        "median_ms": round(statistics.median(samples) * 1000, 3),
        "min_ms": round(min(samples) * 1000, 3),
        "max_ms": round(max(samples) * 1000, 3),
        "p95_ms": round(percentile(samples, 0.95) * 1000, 3)
        if percentile(samples, 0.95) is not None
        else None,
        "p99_ms": round(percentile(samples, 0.99) * 1000, 3)
        if percentile(samples, 0.99) is not None
        else None,
        "sql_statements_median": statistics.median(query_counts),
        "sql_statements_min": min(query_counts),
        "sql_statements_max": max(query_counts),
        "latency_samples_ms": [round(sample * 1000, 3) for sample in samples],
        "sql_statement_samples": query_counts,
    }


def seeded_uuid(generator: random.Random) -> UUID:
    """Return a repeatable UUID from the supplied deterministic generator."""
    return UUID(int=generator.getrandbits(128))


def seed_dataset(
    connection_factory: Any, size: int, history_events: int, seed: int
) -> tuple[list[str], str]:
    generator = random.Random(seed)
    run_id = seeded_uuid(generator).hex
    workflow_id = seeded_uuid(generator)
    execution_ids = [str(seeded_uuid(generator)) for _ in range(size)]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    started_at = now - timedelta(hours=1)

    with connection_factory() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO executions
                    (id, workflow_id, workflow_version_id, current_step, state, attempt,
                     started_at, finished_at, last_outcome, last_operation_id,
                     last_idempotency_proven, last_retryable, tenant_id)
                VALUES (%s, %s, NULL, 0, %s, 1, %s, NULL, NULL, NULL, FALSE, FALSE, NULL)
                """,
                [
                    (execution_id, workflow_id, ExecutionState.RUNNING.value, started_at)
                    for execution_id in execution_ids
                ],
            )
            history_rows = []
            for execution_id in execution_ids:
                for sequence in range(1, history_events + 1):
                    event_type = "execution.retrying" if sequence == history_events and sequence > 1 else "execution.started"
                    history_rows.append(
                        (
                            execution_id,
                            None,
                            workflow_id,
                            sequence,
                            event_type,
                            ExecutionState.RUNNING.value,
                            1,
                            started_at,
                            None,
                            None,
                            None,
                            False,
                        )
                    )
            cursor.executemany(
                """
                INSERT INTO execution_history
                    (execution_id, tenant_id, workflow_id, sequence, event_type, state, attempt,
                     occurred_at, outcome, operation_id, diagnostic, retryable)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                history_rows,
            )
        connection.commit()

    return execution_ids, run_id


def measure(
    operation: Any,
    counter: QueryCounter,
    repetitions: int,
    warmup: int,
    before_each: Any | None = None,
) -> dict[str, Any]:
    for _ in range(warmup):
        if before_each is not None:
            before_each()
        counter.statements = 0
        operation()
    samples: list[float] = []
    queries: list[int] = []
    for _ in range(repetitions):
        if before_each is not None:
            before_each()
        counter.statements = 0
        started = time.perf_counter()
        operation()
        samples.append(time.perf_counter() - started)
        queries.append(counter.statements)
    return summarize(samples, queries)


def reset_recovery_dataset(connection_factory: Any, execution_ids: list[str]) -> None:
    with connection_factory() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM execution_history WHERE execution_id = ANY(%s::uuid[]) AND event_type = 'execution.recovered_stale'",
                (execution_ids,),
            )
            cursor.execute(
                "UPDATE executions SET state = %s, finished_at = NULL WHERE id = ANY(%s::uuid[])",
                (ExecutionState.RUNNING.value, execution_ids),
            )
        connection.commit()


def correctness_passed(correctness: dict[str, Any]) -> bool:
    required_invariants = (
        "all_count_matches_seed",
        "metrics_count_matches_seed",
        "metrics_retry_count_matches_seed",
        "recovery_count_matches_seed",
    )
    return all(correctness.get(invariant) is True for invariant in required_invariants)


def run_size(args: argparse.Namespace, schema: str, size: int) -> dict[str, Any]:
    admin_factory = lambda: psycopg.connect(args.database_url)
    with admin_factory() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA "{schema}"')
        connection.commit()

    counter = QueryCounter()

    def counted_factory() -> CountingConnection:
        connection = psycopg.connect(args.database_url, options=f"-c search_path={schema}")
        return CountingConnection(connection, counter)

    try:
        PostgresMigrationRunner(counted_factory).apply()
        execution_ids, _run_id = seed_dataset(counted_factory, size, args.history_events, args.seed)

        with psycopg.connect(args.database_url, options=f"-c search_path={schema}") as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                postgres_version = cursor.fetchone()[0]
            connection.commit()

        executions = PostgresExecutionRepository(counted_factory)
        history = PostgresExecutionHistoryRepository(counted_factory)
        metrics = GetExecutionMetrics(executions, history)
        recovery_one = RecoverStaleExecution(
            executions,
            ExecutionRecoveryPolicy(stale_after=timedelta(minutes=30)),
        )
        recovery_batch = RecoverStaleExecutions(executions, recovery_one)
        window_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        window_end = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=1)

        all_measurement = measure(executions.all, counter, args.repetitions, args.warmup)
        metrics_measurement = measure(
            lambda: metrics.execute(window_start, window_end),
            counter,
            args.repetitions,
            args.warmup,
        )

        recovered: list[Any] = []

        def recover_batch() -> list[Any]:
            nonlocal recovered
            recovered = recovery_batch.execute(
                now=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            return recovered

        recovery_measurement = measure(
            recover_batch,
            counter,
            args.repetitions,
            args.warmup,
            before_each=lambda: reset_recovery_dataset(counted_factory, execution_ids),
        )

        all_execution_count = len(executions.all())
        metrics_after_recovery = metrics.execute(window_start, window_end)

        with counted_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM executions WHERE state = %s",
                    (ExecutionState.FAILED.value,),
                )
                failed_count = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT COUNT(*) FROM execution_history WHERE event_type = 'execution.recovered_stale'"
                )
                recovery_events = int(cursor.fetchone()[0])

        correctness = {
            "seeded_execution_count": size,
            "history_events_per_execution": args.history_events,
            "execution_repository_all_count": all_execution_count,
            "metrics_total_executions_after_recovery": metrics_after_recovery.total_executions,
            "metrics_retry_count_after_recovery": metrics_after_recovery.retry_count,
            "metrics_recovery_count_after_recovery": metrics_after_recovery.recovery_count,
            "recovered_return_count": len(recovered),
            "failed_execution_count_after_recovery": failed_count,
            "recovery_event_count": recovery_events,
            "all_count_matches_seed": all_execution_count == size,
            "metrics_count_matches_seed": metrics_after_recovery.total_executions == size,
            "metrics_retry_count_matches_seed": metrics_after_recovery.retry_count
            == (size if args.history_events > 1 else 0),
            "recovery_count_matches_seed": len(recovered) == size
            and failed_count == size
            and recovery_events == size
            and metrics_after_recovery.recovery_count == size,
            "all_invariants_pass": False,
            "tenant_isolation_scenario": "not_run",
            "idempotency_scenario": "not_run",
        }
        correctness["all_invariants_pass"] = correctness_passed(correctness)

        return {
            "dataset_size": size,
            "postgres_version": postgres_version,
            "measurements": {
                "execution_repository_all": all_measurement,
                "get_execution_metrics": metrics_measurement,
                "recover_stale_batch_single_run": recovery_measurement,
            },
            "correctness": correctness,
        }
    finally:
        with admin_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            connection.commit()


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "protocol": "Automation OS Phase H baseline characterization v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": os.environ.get("GITHUB_SHA") or os.environ.get("AUTOMATION_OS_GIT_COMMIT"),
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "database_host": urlparse(args.database_url).hostname,
            "database_name": urlparse(args.database_url).path.lstrip("/"),
            "repetitions": args.repetitions,
            "seed": args.seed,
            "history_events_per_execution": args.history_events,
            "warmup_samples": args.warmup,
            "notes": [
                "Seed/setup and schema migration are excluded from operation timings.",
                "This first harness measures repository-wide reads, metrics aggregation, and stale recovery only.",
                "p95/p99 are omitted unless at least 20 measured samples are available.",
                "A dedicated random schema is dropped after each dataset run.",
            ],
        },
        "results": [],
    }

    for index, size in enumerate(args.sizes):
        schema = f"automation_os_bench_{uuid4().hex}"
        try:
            result = run_size(args, schema, size)
            report["results"].append(result)
        except Exception as exc:
            report["results"].append(
                {
                    "dataset_size": size,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            report["status"] = "failed"
            break

    report.setdefault("status", "completed")
    if report["status"] == "completed" and any(
        not correctness_passed(result.get("correctness", {}))
        for result in report["results"]
    ):
        report["status"] = "correctness_failed"

    rendered = json.dumps(report, indent=2, default=str)
    print(rendered)
    if args.json_output:
        args.json_output.write_text(rendered + "\n", encoding="utf-8")

    if report["status"] == "failed":
        return 1
    if report["status"] == "correctness_failed":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
