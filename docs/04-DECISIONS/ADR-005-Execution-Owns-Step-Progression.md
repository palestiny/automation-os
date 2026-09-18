# ADR-005: Execution Owns Workflow Step Progression

- Status: Accepted
- Scope: Workflow execution orchestration

## Context

An `Execution` represents the runtime lifecycle of a workflow. It owns the current step, the execution steps, and the lifecycle state of those steps.

The `Orchestrator` coordinates capability execution and routing selection, while `Execution` remains the authoritative owner of runtime progression and its invariants.

With explicit workflow `Transition` objects, the runtime must distinguish between **selecting where to go** and **applying that selected movement**.

## Decision

`Execution` owns runtime step progression, but it does not infer the next workflow step from collection order.

After a successful step:

1. The Orchestrator/application layer determines the eligible `Transition`.
2. The selected target step ID is passed to `Execution.complete_step(next_step_id=...)`.
3. `Execution` validates the selected target before mutating runtime state.
4. `Execution` completes the current execution step.
5. `Execution` applies the validated target.
6. The target execution step is started.
7. A terminal step may be completed without a target because there is no next step; terminality is determined from the Workflow transition graph, not from collection position.
8. Completing a terminal step ends runtime progression by moving the execution cursor past the execution-step collection; it does not advance to the next list element.

For a non-terminal step, omitting `next_step_id` is invalid. This prevents implicit list-order routing from competing with the explicit Transition model.

## Responsibility Boundary

### Execution owns

- Current runtime position.
- Execution-step lifecycle transitions.
- Applying a selected next-step target.
- Validation that the selected target belongs to the execution.
- Domain invariants around runtime progression.
- Retry and lifecycle state of execution steps.

### Orchestrator / application layer owns

- Coordinating workflow execution.
- Dispatching the current capability.
- Providing execution context to capability execution.
- Evaluating routing conditions when required.
- Selecting the eligible Transition.
- Applying retry-policy decisions through the execution aggregate.
- Deciding when orchestration should continue or terminate.

### Workflow owns

- Workflow step definitions.
- Available transitions.
- Structural validity of transition references.
- Definition-time routing structure.

## Alternatives Considered

### Option 1 — Execution owns progression and applies an explicit target

**Selected.**

**Trade-offs:**

- Keeps runtime lifecycle invariants inside the aggregate that owns execution state.
- Makes branching explicit and testable.
- Prevents accidental fallback to list order.
- Requires the application layer to select a target before progression can occur.

### Option 2 — Execution infers the next step from list order

The aggregate could continue using collection order as the default route.

**Trade-offs:**

- Simple for linear workflows.
- But conflicts with explicit Transition routing.
- Makes branching semantics ambiguous.
- Can silently execute the wrong step when a workflow has multiple routes.

Not selected.

### Option 3 — Orchestrator owns progression directly

The orchestrator could mutate `current_step` and execution-step state itself.

**Trade-offs:**

- Keeps the aggregate API smaller.
- But spreads lifecycle invariants into the application layer.
- Makes it easier for different callers to progress an execution inconsistently.
- Weakens Execution's ownership of its runtime state.

Not selected.

## Consequences

- `Execution.complete_step()` remains the domain entry point for successful step progression.
- The next target is explicit for every non-terminal progression.
- The Orchestrator can later delegate condition evaluation to a dedicated evaluator without moving runtime ownership out of Execution.
- Linear workflows still work through explicit unconditional Transitions.
- Future routing features must preserve the separation between route selection and runtime progression.

## Related Decisions

- ADR-004: Execution and Step Retry Semantics
- ADR-011: Workflow Transition Routing
