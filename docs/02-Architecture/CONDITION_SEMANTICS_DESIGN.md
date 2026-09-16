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

Conceptually:

```text
Transition
    |
    | condition reference
    v
Condition Evaluator
    |
    | ExecutionContext
    v
true / false
```

The Workflow definition remains free of runtime data.

## Routing Rules

For the first branching slice:

1. A Transition without a condition is unconditional.
2. A Transition with a condition is eligible only when its condition evaluates to `true`.
3. After a successful step, eligible outgoing transitions are evaluated.
4. Exactly one eligible transition must be selected.
5. If no transition is eligible, execution cannot silently guess a path.
6. If more than one transition is eligible, execution cannot silently choose based on collection order.

No-match and multiple-match outcomes are therefore explicit routing errors for the first slice.

This avoids hidden business behavior while the workflow graph model is still being established.

## Scope Constraints

The first slice does not define:

- a general expression language;
- user-authored scripts;
- condition composition (`AND`, `OR`, nested expressions);
- loops;
- parallel branches;
- joins;
- event-triggered routing.

These require separate decisions when concrete requirements exist.

## Next Implementation Gate

The next implementation step is to define the minimal `Transition` domain object and its invariants through RED tests.

The runtime `Execution` routing change must then be designed against those tests rather than modifying `current_step` ad hoc.
