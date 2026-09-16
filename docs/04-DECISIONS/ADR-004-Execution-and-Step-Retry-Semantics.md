# ADR-004: Execution and Step Retry Semantics

- Status: Accepted
- Scope: Workflow execution orchestration

## Context

The execution model currently contains both `Execution.attempt` and `ExecutionStep.attempt`.
A workflow step can fail and be retried without restarting the entire workflow execution.
Using the execution-level attempt counter for step retries makes the model ambiguous and makes
retry policy depend on the wrong lifecycle boundary.

## Decision

Retry counters belong to the lifecycle they measure:

- `Execution.attempt` counts retries of the whole `Execution`.
- `ExecutionStep.attempt` counts attempts of that specific workflow step.
- A retry of one step MUST NOT increment `Execution.attempt`.
- A step retry keeps the `Execution` in `RUNNING` state.
- The failed step transitions `FAILED -> RETRYING -> RUNNING` through the `Execution` aggregate.
- `RetryPolicy` evaluates the current step's attempt count for step-level retries.
- `Orchestrator` decides when to retry a step; `Execution` owns the state transitions and invariants.

Example:

```text
Step 1 -> SUCCESS
Step 2 -> FAIL -> RETRY -> SUCCESS
Step 3 -> SUCCESS

Execution.attempt = 1
Step 1 attempt = 1
Step 2 attempt = 2
Step 3 attempt = 1
```

## Consequences

### Positive

- Retry semantics match the lifecycle being retried.
- Execution-level and step-level retry policies can evolve independently.
- Orchestration remains outside the domain aggregate's decision about which capability to execute.
- Tests can verify retry behavior at the correct boundary.

### Trade-off

The model now exposes two attempt counters with deliberately different meanings. Their names
must remain documented and should not be treated as interchangeable.

## Out of Scope

- Persistence of retry history.
- Retry backoff or scheduling.
- Whole-execution retry orchestration.
- Provider-specific retry behavior.
