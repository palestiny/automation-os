# Phase H — Baseline Measurement Protocol

## Status

**Synthetic CI characterization completed for 100/500/5,000 executions; representative baseline and full resource/backpressure evidence remain uncollected.**

This document defines how Phase H evidence will be gathered. It is not a capacity claim, production SLO, or permission to change runtime behavior. Measurements must be produced by a repeatable harness against a known commit and environment.

## Measurement rules

1. Record the exact Git commit, Python version, PostgreSQL server version, dependency lock/input state, OS/container resources, database configuration, and whether the run is local or CI.
2. Use a disposable database created from the repository's migrations. Never run destructive benchmark setup against a shared or production database.
3. Seed deterministic data with a recorded seed. Report actual row counts, executions per workflow/tenant, and history events per execution.
4. Separate setup/seed time from timed operations. Include warm-up and measured sample counts; preserve raw samples. The harness omits p95 below 20 measured samples and p99 below 100; these are reporting floors, not production capacity guarantees. Do not claim p99 from a small sample.
5. Use an explicit, recorded seed for synthetic identifiers and workload shape. Run each scenario more than once and report run-to-run variation. Do not compare results from different resource limits or database configurations as if they were equivalent.
6. Capture correctness invariants alongside performance: persisted states, history sequence uniqueness/order, idempotent replay result, tenant isolation, and no unintended duplicate execution.
7. Keep application-level timings, database query counts, and whole-process throughput as separate measures. Do not infer database query counts from application method-call counts.
8. Keep CI test success distinct from performance evidence. CI is a correctness gate unless a benchmark job explicitly records controlled, comparable measurements.

## Initial workload matrix

These are proposed characterization points, not targets or expected capacity claims. Adjust only when the available environment cannot support a point, and record the reason.

| Scenario | Dataset / concurrency sweep | Measurements |
|---|---|---|
| Execution create/start and state read | 100, 1,000, and 10,000 persisted executions where practical; concurrency 1, 4, and 16 | operation latency, successful operations/sec, errors, SQL statements per operation |
| Execution history append/read | histories with 1, 5, and 20 events per execution; include a growing-history case | append/read latency, SQL statements, rows read/written, transaction duration |
| Idempotent replay | repeated identical idempotency key and distinct keys | replay latency, database operations, duplicate execution count (must remain zero for a replay) |
| Metrics query | same execution counts with a bounded time window and varying history sizes | total latency, SQL statement count, rows fetched, history reads |
| Stale-execution recovery | no stale rows, sparse stale rows, and high stale-row ratio across increasing execution counts | scan/query behavior, recovered count, latency, state correctness |
| Concurrent history append | existing targeted PostgreSQL race test plus a repeatable contention run | success/conflict distribution, duplicate sequences (must remain zero), transaction duration |
| Sustained/soak | a documented steady workload for a recorded duration | throughput drift, memory trend, connection use, error rate, state/history invariants |

Do not fabricate unavailable measurements. If a scenario cannot run because a live provider, deployment, or resource monitor is absent, mark it **NOT RUN** with the missing prerequisite.

## Harness contract

The baseline harness should:

- require an explicit disposable PostgreSQL test URL and fail closed when it is missing;
- refuse production-looking database targets and clearly print the target host/database before setup;
- use migrations and deterministic seeding;
- provide named scenarios, dataset sizes, concurrency, duration/sample count, and seed as explicit CLI options;
- emit machine-readable JSON containing environment metadata, configuration, raw or aggregatable samples, query counts, throughput, resource samples where supported, and correctness checks;
- distinguish warm-up from measured samples and record failures rather than silently dropping them;
- avoid introducing a mandatory runtime dependency or instrumentation into production code;
- include a small smoke scenario for correctness, separate from longer manual load/soak scenarios.

The harness `scripts/benchmark_phase_h_postgres.py` currently characterizes atomic execution start persistence, idempotent replay reads, tenant-scoped idempotency/read isolation, repository-wide execution reads, execution metrics aggregation, individual execution aggregate reads, history reads/appends, stale-execution recovery, concurrent history appends competing for the same sequence, execution-start throughput at configurable concurrency levels, a bounded 30-second synthetic soak, and PostgreSQL row-lock backpressure. Throughput measurements record requested/completed operations, errors, SQL statement counts, elapsed time, and operations per second. Results are specific to the recorded disposable PostgreSQL and runner environment, not production capacity claims. It is not yet the complete Phase H harness. Execution aggregate reads include the repository contract’s event-history hydration; history append is measured as a real insert, with reset/setup excluded from timed samples.

The emitted JSON includes a top-level `scenario_coverage` map. Values of `RUN_BY_THIS_HARNESS` identify scenarios this harness actually measures; `NOT_RUN` explicitly identifies Phase H scenarios for which this report provides no evidence. The current CI report passed all emitted correctness invariants on datasets of 100, 500, and 5,000 executions. See [`PHASE_H_EXECUTION_N_PLUS_ONE_EXIT_REVIEW.md`](PHASE_H_EXECUTION_N_PLUS_ONE_EXIT_REVIEW.md) for measured query counts and explicit remaining gaps. A completed harness process is not the same as full Phase H completion.

Example against a local disposable PostgreSQL database:

```powershell
$env:AUTOMATION_OS_BENCHMARK_DATABASE_URL = "postgresql://user:password@localhost:5432/automation_os_benchmark"
python scripts/benchmark_phase_h_postgres.py --confirm-disposable --sizes 100 1000 --repetitions 20 --warmup 3 --seed 20261009 --json-output phase-h-baseline.json
```

The script refuses production-like database names and non-local hosts unless explicitly allowed. It creates a random schema, applies migrations there, seeds only that schema, measures operations with a query-counting connection wrapper, and drops the schema afterward. Review the printed host/database name before running it. Do not use production credentials or a shared database. The regular CI smoke scenario uses small datasets only to verify harness execution. A separate manually dispatched workflow (`phase-h-soak.yml`) currently seeds 100 executions, uses 20 measured repetitions with 3 warm-up runs, sweeps concurrency 1/4/16, and allows a 30/60/120/300-second execution-start soak. It can report p95 under its sample count, but does not reach the harness's 100-sample p99 reporting floor for each five-repetition operation. These GitHub-hosted runner timings are comparative diagnostics, not representative production-capacity evidence. Repeat runs and a controlled local/staging environment are still required before capacity claims.

Before expanding the harness, inspect repository constructors and migration boundaries to reuse supported composition paths rather than duplicating persistence behavior. Benchmark instrumentation must remain outside runtime semantics.

## Measured findings and remaining hypotheses

### Confirmed and remediated in the current Phase H branch

- The initial metrics implementation read execution history once per selected execution. The synthetic PostgreSQL baseline showed SQL statement counts of 201 for 100 executions and 1,001 for 500. The batched implementation now uses 2 statements for metrics at 100, 500, and 5,000 executions in the current characterization.
- The initial stale-recovery path repeatedly loaded/saved execution aggregates. The synthetic baseline showed 1,344 statements for 100 executions and 5,344 for 500. The batched implementation uses 5 statements for 100 and 500 executions, and 8 at 5,000 because it uses bounded write chunks and a final row-lock/history-sequence concurrency guard.
- A regression test verifies that recovery does not overwrite newer history when another worker appends progress while the execution remains `RUNNING`.

These results establish the query-scaling bottleneck for the tested synthetic workload. They do not establish representative production capacity.

### Still to measure

- History append/read latency across histories with 1, 5, and 20 events, including sustained contention.
- HTTP request latency, multi-step workflows, retries/resume, slow external capability providers, and realistic tenant/workflow distributions.
- Connection-pool exhaustion and database/process resource telemetry beyond the current row-lock timeout and Python heap measurements.
- Repeat-run variation in a controlled staging-like environment with documented resource limits.

Any further optimization should still state a measured baseline, correctness risks, and a measurable before/after criterion.

## Required baseline report

For every completed scenario, record:

- commit SHA and environment;
- scenario and all workload parameters;
- seed/data cardinalities;
- warm-up and measured sample counts;
- median and supported tail percentiles, with raw samples retained;
- throughput, error/conflict counts, SQL statement counts, rows scanned/fetched, transaction timing, and resource measurements where available;
- correctness checks and any skipped/unavailable measures;
- repeat-run variation and interpretation limits.

The first report should rank findings by measured impact and confidence, then propose (not silently implement) any runtime changes. Phase H exit criteria remain those in the scalability/performance design gate. The harness offers an opt-in bounded execution-start soak via `--soak-seconds` (1–300 seconds); it records latency, operation/error counts, SQL statements, and Python heap metrics from `tracemalloc`. This is not process RSS and does not establish production capacity. The harness separately measures bounded PostgreSQL row-lock contention and a benchmark-only `psycopg_pool` client-pool saturation scenario (one slot, 250 ms checkout timeout), including recovery after a slot is released. The latter does not test PostgreSQL server-wide `max_connections` exhaustion. Without the soak flag, the soak scenario is marked `NOT_RUN`.

### Connection-pool saturation scenario

The CI workflow installs `psycopg-pool` only for the benchmark job; it is not added to application runtime requirements and does not change application pool configuration. The scenario holds the single available pool slot, asserts a competing checkout times out within a bounded window, releases the slot, and asserts a subsequent `SELECT 1` succeeds. The JSON report records pool size, configured checkout timeout, observed wait, timeout result, recovery result, and invariant status. This is a deterministic client-pool behavior check, not server connection-limit exhaustion or production capacity evidence.
