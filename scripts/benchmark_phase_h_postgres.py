from __future__ import annotations

import argparse
import json
import os
import platform
import random
import statistics
import sys
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier
from typing import Any
from urllib.parse import urlparse
from uuid import UUID, uuid4

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.execution_metrics import GetExecutionMetrics
from app.application.execution_recovery import (
    ExecutionRecoveryPolicy,
    RecoverStaleExecution,
    RecoverStaleExecutions,
)
from app.domain.execution import Execution, ExecutionState
from app.domain.execution_event import ExecutionEvent
from app.infrastructure.persistence.migrations import PostgresMigrationRunner
from app.infrastructure.persistence.postgres import (
    PostgresExecutionHistoryRepository,
    PostgresExecutionRepository,
    PostgresExecutionStartRepository,
)

PHASE_H_SCENARIO_COVERAGE = {
    "execution_repository_all": "RUN_BY_THIS_HARNESS",
    "get_execution_metrics": "RUN_BY_THIS_HARNESS",
    "recover_stale_batch_single_run": "RUN_BY_THIS_HARNESS",
    "execution_start": "RUN_BY_THIS_HARNESS",
    "execution_state_read": "RUN_BY_THIS_HARNESS",
    "history_append_read": "RUN_BY_THIS_HARNESS",
    "idempotent_replay": "RUN_BY_THIS_HARNESS",
    "tenant_isolation": "RUN_BY_THIS_HARNESS",
    "concurrency": "RUN_BY_THIS_HARNESS",
    "throughput": "RUN_BY_THIS_HARNESS",
    "resource_backpressure": "RUN_BY_THIS_HARNESS",
    "load_soak": "NOT_RUN",
}


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


def report_progress(message: str) -> None:
    """Emit flushed progress so long benchmark stages are observable in CI logs."""
    print(f"[phase-h] {message}", file=sys.stderr, flush=True)


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
    parser.add_argument("--concurrency", type=int, nargs="+", default=[1, 4, 16])
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--soak-seconds", type=int, default=0, help="Opt-in bounded execution-start soak duration (0 disables; maximum 300 seconds).")
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
    if not args.concurrency or any(value < 1 or value > 32 for value in args.concurrency):
        parser.error("--concurrency must contain values between 1 and 32")
    if len(set(args.concurrency)) != len(args.concurrency):
        parser.error("--concurrency must not contain duplicates")
    if args.warmup < 0 or args.warmup > 100:
        parser.error("--warmup must be between 0 and 100")
    if args.soak_seconds < 0 or args.soak_seconds > 300:
        parser.error("--soak-seconds must be between 0 and 300")
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
    if parsed.scheme not in {"postgres", "postgresql"}:
        parser.error("database URL scheme must be postgres or postgresql")
    if host not in {"localhost", "127.0.0.1", "::1", "postgres"} and not args.allow_nonlocal_host:
        parser.error("non-local host refused; inspect the target and pass --allow-nonlocal-host only for a disposable environment")

    return args


def percentile(samples: list[float], fraction: float) -> float | None:
    """Return an order-statistic percentile only when its sample floor is met.

    p95 uses a minimum of 20 observations; p99 uses at least 100. These are
    reporting floors, not a claim that a small benchmark predicts production
    tail latency. Keep the raw samples available for independent analysis.
    """
    if not 0 <= fraction <= 1:
        raise ValueError("fraction must be between 0 and 1")
    minimum_samples = 100 if fraction >= 0.99 else 20
    if len(samples) < minimum_samples:
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
) -> tuple[list[str], str, UUID]:
    generator = random.Random(seed)
    run_id = seeded_uuid(generator).hex
    workflow_id = seeded_uuid(generator)
    execution_ids = [str(seeded_uuid(generator)) for _ in range(size)]
    now = datetime.now(timezone.utc)
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

    return execution_ids, run_id, workflow_id


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
    for index in range(repetitions):
        if index % 10 == 0:
            report_progress(f"measurement sample {index + 1}/{repetitions}")
        if before_each is not None:
            before_each()
        counter.statements = 0
        started = time.perf_counter()
        operation()
        samples.append(time.perf_counter() - started)
        queries.append(counter.statements)
    report_progress(f"measurement completed {repetitions}/{repetitions} samples")
    return summarize(samples, queries)


def reset_history_append_sample(
    connection_factory: Any, execution_id: UUID, sequence: int
) -> None:
    """Remove the prior measured append so each timed append is a real insert."""
    with connection_factory() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM execution_history WHERE execution_id = %s AND sequence = %s",
                (execution_id, sequence),
            )
        connection.commit()


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


def run_resource_backpressure(
    database_url: str,
    schema: str,
    execution_id: UUID,
) -> dict[str, Any]:
    """Verify bounded lock-timeout behavior under deliberate row-lock pressure."""
    options = f"-c search_path={schema} -c statement_timeout=5000 -c lock_timeout=3000"
    contender_options = f"-c search_path={schema} -c statement_timeout=2000 -c lock_timeout=200ms"
    blocker = psycopg.connect(database_url, connect_timeout=5, options=options)
    contender = psycopg.connect(database_url, connect_timeout=5, options=contender_options)
    before: tuple[Any, Any] | None = None
    started = time.perf_counter()
    lock_timeout_observed = False
    try:
        with blocker.cursor() as cursor:
            cursor.execute(
                "SELECT state, current_step FROM executions WHERE id = %s FOR UPDATE",
                (execution_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Backpressure target execution was not found")
            before = (row[0], row[1])

        try:
            with contender.cursor() as cursor:
                cursor.execute(
                    "UPDATE executions SET current_step = current_step WHERE id = %s",
                    (execution_id,),
                )
            contender.commit()
        except psycopg.errors.LockNotAvailable:
            contender.rollback()
            lock_timeout_observed = True
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    finally:
        contender.rollback()
        blocker.rollback()
        contender.close()
        blocker.close()

    with psycopg.connect(
        database_url,
        connect_timeout=5,
        options=f"-c search_path={schema} -c statement_timeout=5000 -c lock_timeout=3000",
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT state, current_step FROM executions WHERE id = %s",
                (execution_id,),
            )
            after_row = cursor.fetchone()
        connection.commit()

    unchanged = before is not None and after_row is not None and before == tuple(after_row)
    return {
        "status": "PASSED" if lock_timeout_observed and unchanged else "FAILED",
        "mode": "bounded PostgreSQL row-lock contention; not connection-pool exhaustion",
        "lock_timeout_observed": lock_timeout_observed,
        "elapsed_ms": elapsed_ms,
        "execution_state_unchanged": unchanged,
        "invariants_pass": lock_timeout_observed and unchanged,
    }


def run_concurrent_history_races(
    database_url: str,
    schema: str,
    connection_factory: Any,
    repetitions: int,
    seed: int,
) -> dict[str, Any]:
    """Characterize concurrent appends competing for one history sequence."""
    generator = random.Random(seed)
    history = PostgresExecutionHistoryRepository(connection_factory)
    executions: list[Execution] = []
    for _ in range(repetitions):
        execution = Execution.create(
            workflow_id=seeded_uuid(generator), execution_id=seeded_uuid(generator)
        )
        execution.start()
        history.append(execution.events[0])
        executions.append(execution)

    race_results: list[dict[str, Any]] = []
    for index, execution in enumerate(executions):
        if index % 10 == 0:
            report_progress(f"history race progress: {index}/{repetitions}")
        counters = (QueryCounter(), QueryCounter())
        factories = tuple(
            (lambda counter=counter: CountingConnection(
                psycopg.connect(database_url, connect_timeout=5, options=f"-c search_path={schema} -c statement_timeout=10000 -c lock_timeout=3000"), counter
            ))
            for counter in counters
        )
        repositories = tuple(PostgresExecutionHistoryRepository(factory) for factory in factories)
        barrier = Barrier(2)
        occurred_at = datetime.now(timezone.utc)
        events = (
            ExecutionEvent(
                execution_id=execution.id, workflow_id=execution.workflow_id, sequence=2,
                event_type=f"benchmark.concurrent.a.{index}", state=ExecutionState.RUNNING,
                attempt=1, occurred_at=occurred_at,
            ),
            ExecutionEvent(
                execution_id=execution.id, workflow_id=execution.workflow_id, sequence=2,
                event_type=f"benchmark.concurrent.b.{index}", state=ExecutionState.RUNNING,
                attempt=1, occurred_at=occurred_at,
            ),
        )

        def append(
            event: ExecutionEvent,
            repository: Any,
            counter: QueryCounter,
            barrier: Barrier = barrier,
        ) -> dict[str, Any]:
            barrier.wait(timeout=10)
            started = time.perf_counter()
            try:
                repository.append(event)
                outcome = "committed"
            except psycopg.errors.UniqueViolation:
                outcome = "unique_violation"
            except ValueError as exc:
                expected_conflicts = (
                    "sequence must be appended in order",
                    "sequence already contains a different event",
                )
                if not any(message in str(exc) for message in expected_conflicts):
                    raise
                outcome = "sequence_conflict"
            return {
                "outcome": outcome,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "sql_statements": counter.statements,
            }

        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda args: append(*args), zip(events, repositories, counters, strict=True)))
        wall_ms = round((time.perf_counter() - started) * 1000, 3)
        persisted = history.list(execution.id)
        outcome_names = [item["outcome"] for item in outcomes]
        invariant_passed = (
            outcome_names.count("committed") == 1
            and sum(outcome in {"unique_violation", "sequence_conflict"} for outcome in outcome_names) == 1
            and [event.sequence for event in persisted] == [1, 2]
            and len({event.sequence for event in persisted}) == len(persisted)
            and persisted[1].event_type in {events[0].event_type, events[1].event_type}
        )
        race_results.append({
            "race_index": index,
            "outcomes": outcome_names,
            "sql_statements": sum(item["sql_statements"] for item in outcomes),
            "wall_duration_ms": wall_ms,
            "worker_elapsed_ms": [item["elapsed_ms"] for item in outcomes],
            "persisted_sequences": [event.sequence for event in persisted],
            "invariants_pass": invariant_passed,
        })

    report_progress(f"history race progress: {len(race_results)}/{repetitions} complete")
    return {
        "race_count": len(race_results),
        "successful_appends": sum(item["outcomes"].count("committed") for item in race_results),
        "conflict_count": sum(sum(outcome in {"unique_violation", "sequence_conflict"} for outcome in item["outcomes"]) for item in race_results),
        "sql_statement_samples_per_race": [item["sql_statements"] for item in race_results],
        "race_wall_duration_samples_ms": [item["wall_duration_ms"] for item in race_results],
        "raw_races": race_results,
        "invariants_pass": len(race_results) == repetitions and all(item["invariants_pass"] for item in race_results),
        "latency_note": "Concurrent wall times are diagnostic for this bounded race only, not production throughput or capacity evidence.",
    }


def run_start_throughput(
    database_url: str,
    schema: str,
    workflow_id: UUID,
    operations_per_worker: int,
    concurrency_levels: list[int],
    seed: int,
) -> dict[str, Any]:
    """Measure persisted execution-start throughput at bounded worker counts."""
    results: list[dict[str, Any]] = []
    for workers in concurrency_levels:
        counters = [QueryCounter() for _ in range(workers)]

        def run_worker(
            worker_index: int,
            counters: list[QueryCounter] = counters,
            workers: int = workers,
        ) -> dict[str, Any]:
            counter = counters[worker_index]
            generator = random.Random(seed + worker_index + workers * 1009)

            def worker_factory() -> CountingConnection:
                connection = psycopg.connect(database_url, connect_timeout=5, options=f"-c search_path={schema} -c statement_timeout=10000 -c lock_timeout=3000")
                return CountingConnection(connection, counter)

            repository = PostgresExecutionStartRepository(worker_factory)
            created_count = 0
            errors = 0
            for operation_index in range(operations_per_worker):
                execution = Execution.create(
                    workflow_id=workflow_id,
                    execution_id=seeded_uuid(generator),
                )
                execution.start()
                _, created = repository.save_idempotent(
                    execution,
                    f"phase-h-throughput-{schema}-{workers}-{worker_index}-{operation_index}",
                )
                if created:
                    created_count += 1
                else:
                    errors += 1
            return {"created": created_count, "errors": errors}

        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            worker_results = list(pool.map(run_worker, range(workers)))
        duration = time.perf_counter() - started
        requested = workers * operations_per_worker
        completed = sum(item["created"] for item in worker_results)
        errors = sum(item["errors"] for item in worker_results)
        results.append({
            "concurrency": workers,
            "operations_per_worker": operations_per_worker,
            "operations_requested": requested,
            "operations_completed": completed,
            "errors": errors,
            "duration_seconds": round(duration, 6),
            "operations_per_second": round(completed / duration, 3) if duration > 0 else 0.0,
            "sql_statement_count": sum(counter.statements for counter in counters),
            "worker_results": worker_results,
            "invariants_pass": completed == requested and errors == 0,
        })

    return {
        "concurrency_levels": list(concurrency_levels),
        "operations_per_worker": operations_per_worker,
        "results": results,
        "total_operations_completed": sum(item["operations_completed"] for item in results),
        "invariants_pass": all(item["invariants_pass"] for item in results),
        "interpretation_note": "Throughput is specific to this disposable PostgreSQL and runner configuration; it is not a production capacity claim.",
    }


def run_start_soak(
    database_url: str,
    schema: str,
    workflow_id: UUID,
    duration_seconds: int,
    workers: int,
    seed: int,
) -> dict[str, Any]:
    """Run an opt-in, bounded execution-start soak with per-worker samples.

    Python heap metrics come from tracemalloc; they are not process RSS or a
    substitute for container/OS memory telemetry. This scenario does not test
    database exhaustion or general backpressure.
    """
    if duration_seconds <= 0:
        return {"status": "NOT_RUN", "reason": "--soak-seconds was not enabled"}

    counters = [QueryCounter() for _ in range(workers)]
    deadline = time.monotonic() + duration_seconds
    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    tracemalloc.reset_peak()
    heap_start, _ = tracemalloc.get_traced_memory()

    def run_worker(worker_index: int) -> dict[str, Any]:
        counter = counters[worker_index]
        generator = random.Random(seed + worker_index * 7919)

        def worker_factory() -> CountingConnection:
            connection = psycopg.connect(database_url, connect_timeout=5, options=f"-c search_path={schema} -c statement_timeout=10000 -c lock_timeout=3000")
            return CountingConnection(connection, counter)

        repository = PostgresExecutionStartRepository(worker_factory)
        latencies: list[float] = []
        completed = 0
        attempted = 0
        errors: list[str] = []
        while time.monotonic() < deadline:
            execution = Execution.create(
                workflow_id=workflow_id,
                execution_id=seeded_uuid(generator),
            )
            execution.start()
            key = f"phase-h-soak-{schema}-{worker_index}-{attempted}"
            attempted += 1
            started = time.perf_counter()
            try:
                _record, created = repository.save_idempotent(execution, key)
                latencies.append(time.perf_counter() - started)
                if not created:
                    errors.append("idempotency key unexpectedly replayed")
                else:
                    completed += 1
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: {exc}")
        return {
            "worker": worker_index,
            "completed": completed,
            "errors": errors,
            "latency_samples_seconds": latencies,
            "sql_statement_count": counter.statements,
        }

    started = time.perf_counter()
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            worker_results = list(pool.map(run_worker, range(workers)))
        elapsed = time.perf_counter() - started
        heap_end, heap_peak = tracemalloc.get_traced_memory()
        samples = [value for result in worker_results for value in result["latency_samples_seconds"]]
        error_count = sum(len(result["errors"]) for result in worker_results)
        completed = sum(result["completed"] for result in worker_results)
        return {
            "status": "completed",
            "requested_duration_seconds": duration_seconds,
            "actual_duration_seconds": round(elapsed, 3),
            "concurrency": workers,
            "operations_completed": completed,
            "error_count": error_count,
            "errors_sample": [error for result in worker_results for error in result["errors"]][:20],
            "operations_per_second": round(completed / elapsed, 3) if elapsed else 0.0,
            "latency": {
                "sample_count": len(samples),
                "median_ms": round(statistics.median(samples) * 1000, 3),
                "min_ms": round(min(samples) * 1000, 3),
                "max_ms": round(max(samples) * 1000, 3),
                "p95_ms": round(percentile(samples, 0.95) * 1000, 3) if percentile(samples, 0.95) is not None else None,
                "p99_ms": round(percentile(samples, 0.99) * 1000, 3) if percentile(samples, 0.99) is not None else None,
                "latency_samples_ms": [round(sample * 1000, 3) for sample in samples],
            } if samples else None,
            "sql_statement_count": sum(result["sql_statement_count"] for result in worker_results),
            "python_heap_start_bytes": heap_start,
            "python_heap_end_bytes": heap_end,
            "python_heap_peak_bytes": heap_peak,
            "python_heap_growth_bytes": heap_end - heap_start,
            "worker_results": [
                {key: value for key, value in result.items() if key != "latency_samples_seconds"}
                | {"latency_sample_count": len(result["latency_samples_seconds"])}
                for result in worker_results
            ],
            "invariants_pass": completed > 0 and error_count == 0 and len(samples) == completed,
            "interpretation_note": "Opt-in synthetic execution-start soak only. Python heap metrics are tracemalloc data, not RSS; no database exhaustion/backpressure or production capacity claim is measured.",
        }
    finally:
        if not was_tracing and tracemalloc.is_tracing():
            tracemalloc.stop()


def correctness_passed(correctness: dict[str, Any]) -> bool:
    required_invariants = (
        "all_count_matches_expected",
        "metrics_count_matches_expected",
        "metrics_retry_count_matches_seed",
        "recovery_count_matches_seed",
        "state_read_matches_seed",
        "history_read_matches_seed",
        "history_append_sequence_valid",
        "execution_start_matches_count",
        "idempotent_replay_same_execution",
        "tenant_isolation_holds",
        "concurrency_invariants_pass",
        "throughput_invariants_pass",
        "resource_backpressure_invariants_pass",
    )
    if not all(correctness.get(invariant) is True for invariant in required_invariants):
        return False

    # An explicitly unrun optional scenario is not a passing result or a failure.
    # Missing status remains fail-closed for callers that do not declare coverage.
    if correctness.get("load_soak_status") == "NOT_RUN":
        return True
    return correctness.get("load_soak_invariants_pass") is True


def run_size(args: argparse.Namespace, schema: str, size: int) -> dict[str, Any]:
    admin_factory = lambda: psycopg.connect(args.database_url, connect_timeout=5, options="-c statement_timeout=10000 -c lock_timeout=3000")
    with admin_factory() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA "{schema}"')
        connection.commit()

    counter = QueryCounter()

    def counted_factory() -> CountingConnection:
        connection = psycopg.connect(args.database_url, connect_timeout=5, options=f"-c search_path={schema} -c statement_timeout=10000 -c lock_timeout=3000")
        return CountingConnection(connection, counter)

    try:
        report_progress(f"dataset={size}: applying migrations")
        PostgresMigrationRunner(counted_factory).apply()
        report_progress(f"dataset={size}: seeding executions and history")
        execution_ids, _run_id, workflow_id = seed_dataset(counted_factory, size, args.history_events, args.seed)

        with psycopg.connect(args.database_url, connect_timeout=5, options=f"-c search_path={schema} -c statement_timeout=10000 -c lock_timeout=3000") as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                postgres_version = cursor.fetchone()[0]
            connection.commit()

        executions = PostgresExecutionRepository(counted_factory)
        history = PostgresExecutionHistoryRepository(counted_factory)
        start_repository = PostgresExecutionStartRepository(counted_factory)
        metrics = GetExecutionMetrics(executions, history)
        recovery_one = RecoverStaleExecution(
            executions,
            ExecutionRecoveryPolicy(stale_after=timedelta(minutes=30)),
        )
        recovery_batch = RecoverStaleExecutions(executions, recovery_one)
        window_start = datetime.now(timezone.utc) - timedelta(days=1)
        window_end = datetime.now(timezone.utc) + timedelta(minutes=1)

        report_progress(f"dataset={size}: measuring execution_repository_all")
        all_measurement = measure(executions.all, counter, args.repetitions, args.warmup)
        report_progress(f"dataset={size}: measuring execution metrics aggregation")
        metrics_measurement = measure(
            lambda: metrics.execute(window_start, window_end),
            counter,
            args.repetitions,
            args.warmup,
        )

        # Exercise the real atomic start persistence boundary with unique keys and
        # deterministic synthetic IDs. The benchmark does not call a fake repository.
        start_generator = random.Random(args.seed + size + 17)
        start_counter = 0
        started_records: list[Any] = []

        def start_execution() -> None:
            nonlocal start_counter
            start_counter += 1
            execution = Execution.create(
                workflow_id=workflow_id,
                execution_id=seeded_uuid(start_generator),
            )
            execution.start()
            record, created = start_repository.save_idempotent(
                execution, f"phase-h-start-{schema}-{start_counter}"
            )
            started_records.append((record, created))

        report_progress(f"dataset={size}: measuring atomic execution start")
        execution_start_measurement = measure(
            start_execution, counter, args.repetitions, args.warmup
        )
        report_progress(f"dataset={size}: measuring throughput at concurrency={args.concurrency}")
        throughput_measurement = run_start_throughput(
            args.database_url,
            schema,
            workflow_id,
            args.repetitions,
            args.concurrency,
            args.seed + size + 211,
        )
        report_progress(f"dataset={size}: running bounded soak seconds={args.soak_seconds}")
        soak_measurement = run_start_soak(
            args.database_url,
            schema,
            workflow_id,
            args.soak_seconds,
            max(args.concurrency),
            args.seed + size + 313,
        )

        replay_workflow_id = workflow_id
        replay_execution = Execution.create(
            workflow_id=replay_workflow_id,
            execution_id=seeded_uuid(start_generator),
        )
        replay_execution.start()
        replay_key = f"phase-h-replay-{schema}"
        replay_record, replay_created = start_repository.save_idempotent(replay_execution, replay_key)
        replay_result: list[Any] = []

        def replay_idempotent_start() -> None:
            candidate = Execution.create(
                workflow_id=replay_workflow_id,
                execution_id=seeded_uuid(start_generator),
            )
            candidate.start()
            replay_result.append(start_repository.save_idempotent(candidate, replay_key))

        report_progress(f"dataset={size}: measuring idempotent replay")
        idempotent_replay_measurement = measure(
            replay_idempotent_start, counter, args.repetitions, args.warmup
        )

        # Same caller-visible idempotency key in two tenant scopes must bind to
        # independent executions, and tenant A must not read tenant B's data.
        report_progress(f"dataset={size}: verifying tenant isolation")
        tenant_a = seeded_uuid(start_generator)
        tenant_b = seeded_uuid(start_generator)
        tenant_key = f"phase-h-tenant-key-{schema}"
        tenant_a_repo = PostgresExecutionStartRepository(counted_factory, tenant_id=tenant_a)
        tenant_b_repo = PostgresExecutionStartRepository(counted_factory, tenant_id=tenant_b)
        tenant_a_execution = Execution.create(
            workflow_id=replay_workflow_id, execution_id=seeded_uuid(start_generator), tenant_id=tenant_a
        )
        tenant_a_execution.start()
        tenant_a_record, tenant_a_created = tenant_a_repo.save_idempotent(tenant_a_execution, tenant_key)
        tenant_b_execution = Execution.create(
            workflow_id=replay_workflow_id, execution_id=seeded_uuid(start_generator), tenant_id=tenant_b
        )
        tenant_b_execution.start()
        tenant_b_record, tenant_b_created = tenant_b_repo.save_idempotent(tenant_b_execution, tenant_key)
        report_progress(f"dataset={size}: isolation checkpoint 1/4 — same key reserved independently")
        tenant_a_replay = tenant_a_repo.get_idempotent(tenant_key, replay_workflow_id)
        tenant_b_replay = tenant_b_repo.get_idempotent(tenant_key, replay_workflow_id)
        report_progress(f"dataset={size}: isolation checkpoint 2/4 — tenant-scoped idempotency replay read")
        tenant_a_execution_repo = PostgresExecutionRepository(counted_factory, tenant_id=tenant_a)
        tenant_a_history_repo = PostgresExecutionHistoryRepository(counted_factory, tenant_id=tenant_a)
        tenant_a_cannot_read_execution = tenant_a_execution_repo.get(tenant_b_execution.id) is None
        report_progress(f"dataset={size}: isolation checkpoint 3/4 — cross-tenant execution read checked")
        tenant_a_cannot_read_history = tenant_a_history_repo.list(tenant_b_execution.id) == ()
        report_progress(f"dataset={size}: isolation checkpoint 4/4 — cross-tenant history read checked")
        tenant_isolation_holds = (
            tenant_a_created and tenant_b_created
            and tenant_a_record.execution_id != tenant_b_record.execution_id
            and tenant_a_replay is not None and tenant_a_replay.id == tenant_a_execution.id
            and tenant_b_replay is not None and tenant_b_replay.id == tenant_b_execution.id
            and tenant_a_cannot_read_execution
            and tenant_a_cannot_read_history
        )

        target_execution_id = UUID(execution_ids[0])
        report_progress(f"dataset={size}: verifying bounded database lock backpressure")
        resource_backpressure = run_resource_backpressure(
            args.database_url,
            schema,
            target_execution_id,
        )
        state_read_result: list[Any] = []

        def read_execution_state() -> None:
            state_read_result[:] = [executions.get(target_execution_id)]

        report_progress(f"dataset={size}: measuring execution state reads")
        state_read_measurement = measure(
            read_execution_state, counter, args.repetitions, args.warmup
        )

        history_read_result: list[Any] = []

        def read_execution_history() -> None:
            history_read_result[:] = [history.list(target_execution_id)]

        report_progress(f"dataset={size}: measuring history reads")
        history_read_measurement = measure(
            read_execution_history, counter, args.repetitions, args.warmup
        )

        append_sequence = args.history_events + 1
        append_event = ExecutionEvent(
            execution_id=target_execution_id,
            workflow_id=workflow_id,
            sequence=append_sequence,
            event_type="benchmark.history_appended",
            state=ExecutionState.RUNNING,
            attempt=1,
            occurred_at=datetime.now(timezone.utc),
        )

        def append_history_event() -> None:
            history.append(append_event)

        report_progress(f"dataset={size}: measuring history append")
        history_append_measurement = measure(
            append_history_event,
            counter,
            args.repetitions,
            args.warmup,
            before_each=lambda: reset_history_append_sample(
                counted_factory, target_execution_id, append_sequence
            ),
        )
        history_after_append = history.list(target_execution_id)

        recovered: list[Any] = []

        def recover_batch() -> list[Any]:
            nonlocal recovered
            recovered = recovery_batch.execute(
                now=datetime.now(timezone.utc)
            )
            return recovered

        report_progress(f"dataset={size}: measuring stale execution recovery")
        recovery_measurement = measure(
            recover_batch,
            counter,
            args.repetitions,
            args.warmup,
            before_each=lambda: reset_recovery_dataset(counted_factory, execution_ids),
        )

        report_progress(f"dataset={size}: measuring concurrent history append races ({args.repetitions} races)")
        concurrency_measurement = run_concurrent_history_races(
            args.database_url, schema, counted_factory, args.repetitions, args.seed + size + 101
        )

        report_progress(f"dataset={size}: validating correctness invariants")
        all_execution_count = len(executions.all())
        expected_execution_count = size + len(started_records) + 3 + throughput_measurement["total_operations_completed"] + (soak_measurement.get("operations_completed", 0))
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

        replayed_execution = start_repository.get_idempotent(replay_key, replay_workflow_id)
        idempotent_replay_passed = bool(
            replay_result
            and all(
                not created and record.execution_id == replay_record.execution_id
                for record, created in replay_result
            )
            and replay_created
            and replayed_execution is not None
            and replayed_execution.id == replay_record.execution_id
        )

        correctness = {
            "seeded_execution_count": size,
            "expected_total_execution_count": expected_execution_count,
            "history_events_per_execution": args.history_events,
            "execution_repository_all_count": all_execution_count,
            "metrics_total_executions_after_recovery": metrics_after_recovery.total_executions,
            "metrics_retry_count_after_recovery": metrics_after_recovery.retry_count,
            "metrics_recovery_count_after_recovery": metrics_after_recovery.recovery_count,
            "recovered_return_count": len(recovered),
            "failed_execution_count_after_recovery": failed_count,
            "recovery_event_count": recovery_events,
            "all_count_matches_expected": all_execution_count == expected_execution_count,
            "metrics_count_matches_expected": metrics_after_recovery.total_executions == expected_execution_count,
            "metrics_retry_count_matches_seed": metrics_after_recovery.retry_count
            == (size if args.history_events > 1 else 0),
            "recovery_count_matches_seed": len(recovered) == size
            and failed_count == size
            and recovery_events == size
            and metrics_after_recovery.recovery_count == size,
            "state_read_execution_id": str(state_read_result[0].id) if state_read_result and state_read_result[0] else None,
            "state_read_matches_seed": bool(state_read_result and state_read_result[0] and state_read_result[0].id == target_execution_id),
            "history_read_event_count_before_append": len(history_read_result[0]) if history_read_result and history_read_result[0] else 0,
            "history_read_matches_seed": bool(history_read_result and history_read_result[0] and len(history_read_result[0]) == args.history_events),
            "history_append_final_event_count": len(history_after_append),
            "history_append_final_sequence": history_after_append[-1].sequence if history_after_append else None,
            "history_append_sequence_valid": len(history_after_append) == args.history_events + 1 and history_after_append[-1].sequence == append_sequence and history_after_append[-1].event_type == "benchmark.history_appended",
            "execution_start_sample_count": len(started_records),
            "execution_start_created_count": sum(1 for _, created in started_records if created),
            "execution_start_matches_count": len(started_records) == args.repetitions + args.warmup and all(created for _, created in started_records),
            "idempotent_replay_same_execution": idempotent_replay_passed,
            "tenant_isolation_holds": tenant_isolation_holds,
            "concurrency_invariants_pass": concurrency_measurement["invariants_pass"],
            "throughput_invariants_pass": throughput_measurement["invariants_pass"],
            "resource_backpressure_invariants_pass": resource_backpressure["invariants_pass"],
            "resource_backpressure_status": resource_backpressure["status"],
            "load_soak_status": soak_measurement.get("status", "RUN"),
            "load_soak_invariants_pass": (
                soak_measurement.get("invariants_pass")
                if soak_measurement.get("status") != "NOT_RUN"
                else None
            ),
            "all_invariants_pass": False,
            "tenant_isolation_scenario": "passed" if tenant_isolation_holds else "failed",
            "idempotency_scenario": "passed" if idempotent_replay_passed else "failed",
        }
        correctness["all_invariants_pass"] = correctness_passed(correctness)

        return {
            "dataset_size": size,
            "postgres_version": postgres_version,
            "measurements": {
                "execution_repository_all": all_measurement,
                "execution_start": execution_start_measurement,
                "throughput": throughput_measurement,
                "resource_backpressure": resource_backpressure,
                "load_soak": soak_measurement,
                "idempotent_replay": idempotent_replay_measurement,
                "get_execution_metrics": metrics_measurement,
                "execution_state_read": state_read_measurement,
                "history_read": history_read_measurement,
                "history_append": history_append_measurement,
                "recover_stale_batch_single_run": recovery_measurement,
                "concurrency_history_append": concurrency_measurement,
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
    parsed_database_url = urlparse(args.database_url)
    # Show the target before any schema creation, migrations, or seeded writes.
    # Never print the full DSN because it may contain credentials.
    print(
        "Phase H disposable database target: "
        f"host={parsed_database_url.hostname!r}, "
        f"database={parsed_database_url.path.lstrip('/')!r}, "
        f"schema=isolated random schema per dataset; "
        "confirm this is disposable before proceeding.",
        file=sys.stderr,
        flush=True,
    )
    report: dict[str, Any] = {
        "protocol": "Automation OS Phase H baseline characterization v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": os.environ.get("GITHUB_SHA") or os.environ.get("AUTOMATION_OS_GIT_COMMIT"),
        "scenario_coverage": {
            **PHASE_H_SCENARIO_COVERAGE,
            "load_soak": "RUN_BY_THIS_HARNESS" if args.soak_seconds > 0 else "NOT_RUN",
        },
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "database_host": urlparse(args.database_url).hostname,
            "database_name": urlparse(args.database_url).path.lstrip("/"),
            "repetitions": args.repetitions,
            "concurrency_levels": args.concurrency,
            "seed": args.seed,
            "history_events_per_execution": args.history_events,
            "warmup_samples": args.warmup,
            "soak_seconds": args.soak_seconds,
            "notes": [
                "Seed/setup and schema migration are excluded from operation timings.",
                "Scenario coverage is enumerated at scenario_coverage; NOT_RUN entries are not acceptance evidence.",
                "Harness coverage is enumerated per scenario; each implemented scenario records its own correctness evidence.",
                "p95 is omitted below 20 measured samples; p99 is omitted below 100. These are reporting floors, not capacity guarantees.",
                "A dedicated random schema is dropped after each dataset run.",
                "load_soak measures synthetic execution-start persistence; resource_backpressure measures bounded row-lock timeout, not connection-pool exhaustion.",
            ],
        },
        "status": "running",
        "results": [],
    }

    def persist_report_snapshot() -> None:
        if args.json_output is None:
            return
        temporary_path = args.json_output.with_suffix(args.json_output.suffix + ".tmp")
        temporary_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        temporary_path.replace(args.json_output)

    # Persist a checkpoint before work starts so a hard timeout still leaves an artifact.
    persist_report_snapshot()

    for size in args.sizes:
        report_progress(f"starting dataset size={size}; repetitions={args.repetitions}; concurrency={args.concurrency}")
        schema = f"automation_os_bench_{uuid4().hex}"
        try:
            result = run_size(args, schema, size)
            report["results"].append(result)
            persist_report_snapshot()
            report_progress(f"finished dataset size={size}; correctness={result.get('correctness', {}).get('all_invariants_pass')}")
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
            persist_report_snapshot()
            break

    if report["status"] != "failed":
        report["status"] = "completed"
    if report["status"] == "completed" and any(
        not correctness_passed(result.get("correctness", {}))
        for result in report["results"]
    ):
        report["status"] = "correctness_failed"

    rendered = json.dumps(report, indent=2, default=str)
    print(rendered)
    persist_report_snapshot()

    if report["status"] == "failed":
        return 1
    if report["status"] == "correctness_failed":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
