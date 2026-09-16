# ADR-006: Capability Result and Execution Context Flow

- Status: Accepted
- Scope: Workflow execution orchestration

## Context

Capabilities need a way to return successful output to the workflow runtime so that later steps can consume the result. `ExecutionContext` already exists as the runtime container passed to capabilities, but `CapabilityResult` previously represented only success or failure.

Without an explicit output path, step-to-step data flow would remain implicit and the orchestrator would have no defined responsibility for propagating successful capability results.

## Decision

`CapabilityResult` carries the output of a successful capability execution.

The flow is:

```text
Capability
    ↓
CapabilityResult
    ├── succeeded
    ├── output
    └── error (when failed)
            ↓
      Orchestrator
            ↓
   ExecutionContext
            ↓
      Next Capability
```

The `Orchestrator` stores the successful result output in the `ExecutionContext`, keyed by the current `WorkflowStep` identifier. The next capability receives the same context and can read outputs produced by previous steps.

## Responsibility Boundary

### CapabilityResult owns

- Whether capability execution succeeded.
- Successful capability output.
- Failure information when execution fails.

### ExecutionContext owns

- Runtime data shared between capability executions.
- Step-to-step data available during the current orchestration.

### Orchestrator owns

- Moving successful capability output from `CapabilityResult` into `ExecutionContext`.
- Passing the execution context to capability dispatch.
- Coordinating the sequence without becoming the owner of capability business meaning.

### Execution does not own

- Capability output storage.
- Capability-specific data transformation.
- Runtime context storage.

## Alternatives Considered

### Option 1 — CapabilityResult carries output

**Selected.**

**Trade-offs:**

- Makes the capability contract explicit and easy to test.
- Keeps capabilities independent from the orchestration context implementation.
- Gives the orchestrator a clear hand-off point between capability execution and runtime state.
- Requires discipline to keep `CapabilityResult` small as the platform grows.

### Option 2 — Capability writes directly to ExecutionContext

**Not selected.**

**Trade-offs:**

- Can make simple chaining concise.
- But couples capabilities to a specific orchestration runtime object.
- Makes output ownership less explicit and makes capability contracts harder to reason about independently.

### Option 3 — Introduce Asset/Outcome semantics now

**Not selected for this phase.**

**Trade-offs:**

- Would align immediately with the long-term domain model.
- But Asset and Outcome semantics are not sufficiently defined to make them the correct transport contract for current step execution.
- Introducing them now would expand the design surface before the execution engine needs those concepts.

## Consequences

- Successful capability output can flow from one workflow step to another.
- `ExecutionContext` remains application/runtime infrastructure rather than becoming a domain concept.
- Asset/Outcome modeling remains a separate future design gate.
- The current output key is the `WorkflowStep` identifier; a richer context contract can be introduced later if real workflow requirements justify it.

## Open Questions

- Whether context values should eventually be strongly typed.
- Whether outputs should be wrapped in a dedicated value object.
- How Asset instances should enter or leave the execution context.
- Whether execution history should persist step outputs.

These questions are intentionally deferred until workflow data requirements make them concrete.

## Related Decisions

- ADR-005: Execution Owns Workflow Step Progression
