# Condition Semantics — Design Gate

- Status: Design decision committed for first branching slice
- Phase: Phase 3 — Workflow Engine
- Scope: Minimal condition representation and routing behavior

## Decision

The first branching slice will use a **named condition reference** rather than embedding an expression language inside the Workflow definition.

A conditional Transition carries a string `condition` reference. An unconditional Transition carries no condition reference.

Example:

```text
Step A --[is_customer]--> Step B
       --[no_condition]--> Step C
```

The reference is a domain-level identifier for a condition evaluator/definition. The Workflow does not execute or interpret the condition itself.

## Why

This keeps the Workflow definition declarative without prematurely designing an expression language, scripting engine, or provider-specific syntax.

### Trade-offs

**Named reference**

- Pros: small model, explicit boundary, testable, replaceable evaluator, no embedded scripting.
- Cons: condition definitions/evaluator registry must be designed later; the Workflow alone cannot explain the full meaning of a condition reference.

**Inline expression language**

- Pros: self-contained workflow definitions and flexible conditions.
- Cons: requires syntax, parser, type/value semantics, security rules, versioning, and error behavior much earlier.

**Fixed boolean predicate types**

- Pros: strongly controlled semantics.
- Cons: quickly becomes a growing catalog of special cases and couples Workflow to business-specific predicate types.

The named reference is selected for the first slice to preserve a small, replaceable boundary.

## Evaluation Ownership

Condition evaluation belongs at the application/domain-service boundary, not inside `WorkflowStep` or `Transition` as capability-like execution.

The evaluator receives runtime `ExecutionContext` and a condition reference, then returns a boolean result.

For the first implementation slice, the concrete mechanism is an in-memory **ConditionRegistry** that maps a normalized named condition reference to a callable receiving `ExecutionContext` and returning `bool`.

The registry is an evaluator implementation, not a new runtime owner. It owns condition lookup and invocation only; it does not select transitions or mutate `Execution`.

Conceptually:

```text
Transition
    |
    | condition reference
    v
ConditionRegistry / Evaluator
    |
    | ExecutionContext
    v
true / false
```

The Workflow definition remains free of runtime data.

The routing boundary is deliberately split:

- **Condition Evaluator / Registry** answers whether a conditional Transition is eligible.
- **Orchestrator/application layer** selects exactly one eligible Transition and coordinates routing.
- **Execution** applies the selected target and owns runtime progression invariants.

This keeps route selection separate from mutation of runtime execution state.

## Registry Rules

The first registry implementation follows these rules:

1. A condition name must not be blank.
2. A condition name is normalized by trimming surrounding whitespace.
3. A condition name may be registered only once in a registry instance.
4. Evaluating an unregistered condition is an explicit error.
5. A registered condition receives the current `ExecutionContext` and returns `bool`.
6. The registry does not select transitions or mutate execution state.

The registry is intentionally in-memory for this slice. Persistence, dynamic configuration, condition versioning, and user-authored condition definitions are deferred until a concrete requirement exists.

## Routing Rules

For the first branching slice:

1. A Transition without a condition is unconditional.
2. A Transition with a condition is eligible only when its condition evaluates to `true`.
3. After a successful step, eligible outgoing transitions are evaluated.
4. Exactly one eligible transition must be selected.
5. If no transition is eligible, execution cannot silently guess a path.
6. If more than one transition is eligible, execution cannot silently choose based on collection order.
7. A terminal step may complete without a transition.

No-match and multiple-match outcomes are therefore explicit routing errors for the first slice.

## Scope Constraints

The first slice does not define:

- a general expression language;
- user-authored scripts;
- condition composition (`AND`, `OR`, nested expressions);
- loops;
- parallel branches;
- joins;
- event-triggered routing;
- persisted or dynamically authored condition definitions.

These require separate decisions when concrete requirements exist.

## Next Implementation Gate

The minimal registry boundary is implemented and covered by RED → GREEN tests. The next step is to verify the complete suite, then review whether registry errors need dedicated application error types before expanding the workflow engine.
