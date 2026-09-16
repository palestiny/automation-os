# Conditions & Branching — Design Gate

- Status: Core routing and first condition semantics committed
- Phase: Phase 3 — Workflow Engine
- Scope: Conditional workflow progression / branching
- Owner: Khaled (Project Owner / Decision Maker / Tech Lead)

## Purpose

Define the business meaning and ownership boundary of conditional progression before changing the current linear Workflow/Execution model.

## 1. Current Model

A `Workflow` is a reusable definition containing an ordered collection of `WorkflowStep` objects. `Execution` materializes runtime `ExecutionStep` objects and owns runtime progression.

The workflow definition now supports explicit routing through `Transition` objects. This replaces the assumption that runtime progression is always determined by collection order.

## 2. Business Meaning

A condition exists to determine whether an execution should follow one possible path instead of another based on runtime information.

The important distinction is:

- A **step** describes work that can be performed.
- A **transition** describes movement from one step to another.
- A **condition** describes whether a transition is eligible.
- Runtime data used to evaluate a condition belongs to the execution context, not to the published workflow as mutable runtime state.

## 3. Committed Routing Model

The project uses an explicit **Transition/Edge** concept for branching.

Conceptually:

```text
Step A --[condition X]--> Step B
       --[condition !X]--> Step C
```

`WorkflowStep` remains focused on the work definition. Routing is modeled separately.

### Why this model was selected

- A condition naturally belongs to the transition it controls.
- Multiple destinations can be represented without overloading `WorkflowStep`.
- Work and routing remain separate concepts.
- The model can evolve toward richer branching without redefining what a step means.

### Trade-offs accepted

- A new domain concept and additional validation are required.
- Execution progression must support an explicitly selected target.
- Testing and workflow visualization become more involved.

## 4. Responsibilities

### Workflow owns

- The definition of available steps.
- The definition of transitions between steps.
- Structural validity of the workflow definition.

### Execution owns

- Runtime current position.
- Runtime state and attempts.
- Runtime progression after a routing decision.
- Runtime execution-step invariants.

Execution does not infer a non-terminal next step from collection order.

### Orchestrator/application layer owns

- Coordinating condition evaluation during execution.
- Supplying runtime context to the condition evaluator.
- Selecting exactly one eligible transition.
- Passing the selected target to `Execution`.

A condition must not execute capabilities or own the Execution lifecycle.

## 5. Committed Condition Semantics — First Slice

The first branching slice uses a **named condition reference**, not an embedded expression language.

- A conditional `Transition` carries a string `condition` reference.
- An unconditional `Transition` carries `None`.
- The Workflow stores the reference but does not execute or interpret it.
- The evaluator receives `ExecutionContext` plus the condition reference and returns `bool`.

The concrete implementation for this slice is an in-memory **ConditionRegistry** mapping normalized names to callables.

The registry owns lookup and invocation only. It does not select transitions or mutate `Execution`.

### Registry rules

1. Condition names cannot be blank.
2. Surrounding whitespace is trimmed.
3. Duplicate names are rejected within a registry instance.
4. Unknown condition names are explicit errors.
5. Registered conditions receive the current `ExecutionContext` and return `bool`.
6. Persistence, dynamic configuration, versioning, and user-authored condition definitions are deferred.

## 6. Runtime Routing Rules

After a successful step:

1. Outgoing transitions are obtained from the Workflow.
2. Unconditional transitions are eligible.
3. Conditional transitions are evaluated through the condition evaluator.
4. Exactly one eligible transition must exist.
5. If no transition is eligible, routing fails explicitly.
6. If multiple transitions are eligible, routing fails explicitly rather than using collection order.
7. A terminal step may complete without an outgoing transition.
8. A non-terminal step cannot complete without an explicitly selected target.

These rules keep definition semantics and runtime semantics aligned.

## 7. Initial Scope Constraints

The first branching slice does not introduce:

- a general expression language;
- user-authored scripts;
- condition composition (`AND`, `OR`, nested expressions);
- loops;
- parallel branches;
- joins;
- event-triggered routing;
- persisted or dynamically authored condition definitions.

These require separate decisions when concrete requirements exist.

## 8. Error Boundary

The current implementation intentionally uses ordinary `ValueError` for invalid condition registration/evaluation and routing failures.

Dedicated application error types are **not introduced yet** because there is currently no requirement for callers to distinguish these failures programmatically beyond the existing application boundary. Introducing an exception hierarchy now would add API surface without changing the current business behavior.

This decision can be revisited when error translation, API responses, retry classification, observability, or other consumers require stable error categories.

## 9. Decision Status

**Committed:**

- Explicit Transition/Edge routing.
- Named condition references for the first branching slice.
- In-memory ConditionRegistry as the first evaluator implementation.
- ConditionEvaluator boundary receiving `ExecutionContext` and returning `bool`.
- Orchestrator selects exactly one eligible transition.
- Execution applies the selected target and owns runtime progression invariants.
- No-match and multiple-match routing are explicit errors.

**Deferred:**

- Dedicated exception hierarchy.
- Condition persistence/versioning/dynamic configuration.
- Expression language and condition composition.
- Loop policy.
- Rich graph validation beyond current structural endpoint validation.
- Parallel/joins/event-triggered routing.

## Related Documentation

- `docs/02-Architecture/WORKFLOW_DESIGN_GATE.md`
- `docs/02-Architecture/CONDITION_SEMANTICS_DESIGN.md`
- `docs/04-DECISIONS/ADR-005-Execution-Owns-Step-Progression.md`
- `docs/04-DECISIONS/ADR-004-Execution-and-Step-Retry-Semantics.md`
- `docs/04-DECISIONS/ADR-006-Capability-Result-and-Execution-Context-Flow.md`
- `docs/04-DECISIONS/ADR-011-Workflow-Transition-Routing.md`
