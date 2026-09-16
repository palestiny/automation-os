# Conditions & Branching — Design Gate

- Status: Core routing model committed; condition semantics remain scoped for implementation
- Phase: Phase 3 — Workflow Engine
- Scope: Conditional workflow progression / branching
- Owner: Khaled (Project Owner / Decision Maker / Tech Lead)

## Purpose

Define the business meaning and ownership boundary of conditional progression before changing the current linear Workflow/Execution model.

## 1. Current Model

A `Workflow` is a reusable definition containing an ordered collection of `WorkflowStep` objects. `Execution` materializes runtime `ExecutionStep` objects and currently advances by incrementing `current_step`.

This is intentionally linear today:

```text
Step A -> Step B -> Step C
```

The existing Workflow model defines step order, while Execution owns runtime progression. Branching will preserve that ownership boundary while replacing implicit next-step selection with explicit routing where required.

## 2. Business Meaning

A condition exists to determine whether an execution should follow one possible path instead of another based on runtime information.

The important distinction is:

- A **step** describes work that can be performed.
- A **transition** describes movement from one step to another.
- A **condition** describes whether a transition is eligible.
- Runtime data used to evaluate a condition belongs to the execution context, not to the published workflow as mutable runtime state.

## 3. Committed Routing Model — Option B

The project has selected an explicit **Transition/Edge** concept for branching.

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
- Execution progression must evolve beyond simple integer incrementing when explicit branching is used.
- Testing and workflow visualization become more involved.

## 4. Responsibilities

### Workflow owns

- The definition of available steps.
- The definition of transitions between steps.
- Structural validity of the workflow definition.

### Execution owns

- Runtime current position.
- Runtime state and attempts.
- Runtime progression after routing decisions.
- Runtime execution context/data.

### Orchestrator/application layer owns

- Coordinating condition evaluation during execution.
- Supplying runtime context to the condition evaluator.
- Coordinating the selected transition with Execution.

A condition must not execute capabilities or own the Execution lifecycle.

## 5. Initial Scope

The first branching slice will remain intentionally narrow:

- `WorkflowStep` remains an action definition.
- A Transition identifies a source step and destination step.
- A Transition may be unconditional or conditional.
- A condition is evaluated against runtime execution context.
- Execution selects a valid next transition after successful step completion.
- No parallel branches, joins, nested workflows, event triggers, or general-purpose graph engine are introduced in this slice.
- Existing retry semantics remain step-oriented; routing occurs after successful step completion.

## 6. Important Runtime Consequence

The current `Execution.current_step: int` model assumes that the next step is always the next item in the Workflow collection.

With explicit transitions, that assumption is no longer sufficient for arbitrary branching. The runtime model therefore needs a deliberate next-step representation before branching execution is implemented.

This does **not** authorize an ad-hoc rewrite of Execution. The runtime change must be covered by behavior-first tests and its own implementation decision.

## 7. Deferred Condition Semantics

The routing model is committed, but the following are deliberately not committed yet:

1. Whether every transition must have an explicit condition object or whether unconditional transitions are represented directly.
2. The minimum condition language: fixed predicates, named condition objects, or an expression language.
3. The exact evaluator ownership and API.
4. What happens when no transition matches.
5. What happens when multiple transitions match.
6. Whether loops are allowed in the first branching slice.
7. Workflow validation rules for unreachable steps or dead ends.
8. Whether ordinary linear workflows retain implicit collection order as a convenience/default path.

These are implementation-shaping questions and should be resolved before their corresponding behavior is coded.

## 8. Design Constraint

The system must not claim to support branching in the Workflow definition while the runtime still silently follows collection order.

Definition semantics and runtime semantics must move together behind tests.

## 9. Decision Status

**Committed:** explicit Transition/Edge model for workflow routing.

**Deferred:** concrete condition representation, evaluation contract, no-match/multiple-match semantics, loop policy, and graph validation rules.

## Related Documentation

- `docs/02-Architecture/WORKFLOW_DESIGN_GATE.md`
- `docs/04-DECISIONS/ADR-005-Execution-Owns-Step-Progression.md`
- `docs/04-DECISIONS/ADR-004-Execution-and-Step-Retry-Semantics.md`
- `docs/04-DECISIONS/ADR-006-Capability-Result-and-Execution-Context-Flow.md`
