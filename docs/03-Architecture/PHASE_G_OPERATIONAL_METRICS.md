# Phase G — Operational Metrics Boundary

## Decision
Automation OS introduces a small application-owned `OperationalMetrics` port for timing evidence.

The first production-safe slice records:
- `capability.execution` duration;
- normalized capability outcome.

The application layer does not depend on Prometheus, OpenTelemetry, CloudWatch, or another vendor.
A `NoopOperationalMetrics` implementation remains the default when no metrics backend is configured.

## Boundary
`ExecuteWorkflowStep` owns capability execution timing because it is the application boundary that invokes the capability dispatcher.

The metrics sink is observational only:
`capability execution -> timing evidence -> OperationalMetrics`

If the metrics implementation fails, execution continues with its original semantics.

## Data rules
- Metric names are fixed application-owned values.
- The first slice does not emit tenant IDs, execution IDs, workflow IDs, request bodies, connection references, secret references, or credentials.
- Outcome is bounded.

## Deferred adapter decision
A concrete backend is deferred until operational requirements are measured. Candidate adapters include OpenTelemetry metrics, Prometheus-compatible export, or a cloud-native backend.

## Acceptance criteria
1. Capability timing is measured at the application execution boundary.
2. Outcome is included as bounded evidence.
3. Metrics failure cannot alter execution behavior.
4. No sensitive or high-cardinality identifiers are emitted by the first slice.
5. Existing execution semantics remain unchanged.
6. Tests cover the boundary and validation rules.

## Non-goals
This slice does not establish a metrics backend, dashboards, alerting, SLOs, distributed tracing, or autoscaling policy.