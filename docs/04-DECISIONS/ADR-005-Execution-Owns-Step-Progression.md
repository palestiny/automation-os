# ADR-005: Execution Owns Workflow Step Progression

- Status: Accepted
- Scope: Workflow execution orchestration

## Context

An `Execution` represents the runtime lifecycle of a workflow. It owns the current step, the execution steps, and the lifecycle state of those steps.

The `Orchestrator` is responsible for coordinating capability execution, but step progression must have a single clear owner.

## Decision

`Execution` owns workflow step progression.

When `Execution.complete_step()` is called:

1. The current execution step is completed.
2. `current_step` advances to the next workflow step.
3. If another step exists, that next execution step is started.

The `Orchestrator` does not directly mutate `current_step` or start the next step. It dispatches the capability associated with the current workflow step and asks the `Execution` aggregate to apply the resulting lifecycle transition.

## Responsibility Boundary

### Execution owns

- Current-step position.
- Execution-step lifecycle transitions.
- Advancing from a completed step to the next step.
- Domain invariants around execution progression.

### Orchestrator owns

- Coordinating workflow execution.
- Dispatching the current capability.
- Providing execution context to capability execution.
- Applying retry-policy decisions through the execution aggregate.
- Deciding when orchestration should continue or terminate.

## Alternatives Considered

### Option 1 — Execution owns progression

**Selected.**

**Trade-offs:**

- Keeps runtime progression close to the aggregate that owns `current_step` and `steps`.
- Makes domain invariants easier to test in isolation.
- Requires the aggregate to understand execution-step lifecycle, which is appropriate because those are part of its runtime model.

### Option 2 — Orchestrator owns progression

The orchestrator could increment `current_step` and start the next step itself.

**Trade-offs:**

- Keeps the domain aggregate smaller.
- But spreads execution lifecycle rules into the application layer.
- Makes it easier for different callers to progress an execution inconsistently.
- Weakens the aggregate's ownership of its own runtime state.

### Option 3 — Hybrid progression

The orchestrator could partially advance execution while delegating some lifecycle operations to `Execution`.

**Trade-offs:**

- Can appear flexible initially.
- But creates ambiguous ownership and increases the risk of duplicated transition rules.
- Not selected because there is no current requirement that justifies the added boundary complexity.

## Consequences

- `Execution.complete_step()` is the domain entry point for successful step progression.
- The orchestrator remains a coordinator rather than becoming the owner of execution state.
- Tests can verify step progression independently from capability dispatch.
- Future changes to execution progression should begin by evaluating the `Execution` aggregate boundary.

## Related Decisions

- ADR-004: Execution and Step Retry Semantics
