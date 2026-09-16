# Conditions & Branching — Design Gate

- Status: Design decision required before implementation
- Phase: Phase 3 — Workflow Engine
- Scope: Conditional workflow progression / branching
- Owner: Khaled (Project Owner / Decision Maker / Tech Lead)

## Purpose

Define the business meaning and ownership boundary of conditional progression before changing the current linear Workflow/Execution model.

This is a design gate, not an implementation specification. No Execution or Workflow code should be changed for branching until the model is agreed.

## 1. Current Model

A `Workflow` is a reusable definition containing an ordered collection of `WorkflowStep` objects. `Execution` materializes runtime `ExecutionStep` objects and currently advances by incrementing `current_step`.

This is intentionally linear today:

```text
Step A -> Step B -> Step C
```

The existing Workflow model defines step order, while Execution owns runtime progression. Any branching design must preserve that ownership boundary unless a deliberate architecture decision changes it.

## 2. Business Meaning

A condition exists to determine whether an execution should follow one possible path instead of another based on runtime information.

Example:

```text
Step A
  |
  +-- condition true  -> Step B
  |
  +-- condition false -> Step C
```

The important distinction is:

- A **step** describes work that can be performed.
- A **condition** describes a rule used to choose a path.
- Runtime data used to evaluate that rule belongs to the execution context, not to the published workflow as mutable runtime state.

## 3. Responsibilities

### Workflow owns

- The definition of available steps.
- The definition of how steps may connect.
- The definition of conditional routing rules, if the selected model puts routing in the Workflow definition.
- Structural validity of the published workflow definition.

### Execution owns

- Runtime current position.
- Runtime state and attempts.
- Runtime progression after a routing decision has been made.
- Runtime context used by application-level condition evaluation.

### Orchestrator/application layer owns

- Coordinating condition evaluation during execution.
- Supplying the runtime context to the evaluator.
- Asking Execution to perform the resulting progression transition.

A condition should not execute capabilities or own the Execution lifecycle.

## 4. Candidate Models

### Option A — Condition is a property of `WorkflowStep`

A step could carry something such as `condition` describing whether that step should execute.

Conceptually:

```text
Step A
Step B [condition: X]
Step C [condition: not X]
```

**Advantages**

- Small extension to the current model.
- Keeps the existing ordered-step representation.
- Easy to express a simple skip/execute rule.

**Trade-offs**

- The condition is attached to the destination step even though its business meaning is selecting a transition.
- Multiple possible destinations become awkward to model cleanly.
- The model becomes increasingly procedural if future branching needs several paths, joins, or loops.
- `Execution.current_step` as an integer remains insufficient for non-linear routing.

### Option B — Separate transition/edge concept

Keep `WorkflowStep` as the work definition and introduce an explicit relationship describing how execution moves from one step to another.

Conceptually:

```text
Step A --[condition X]--> Step B
Step A --[condition !X]--> Step C
```

**Advantages**

- The condition naturally belongs to the transition it controls.
- Multiple destinations can be represented without overloading `WorkflowStep`.
- The model can evolve toward richer branching without redefining what a step means.
- Separates work (`WorkflowStep`) from routing (`Transition`).

**Trade-offs**

- Adds a new domain concept and more validation.
- The current ordered-list model cannot remain the sole source of progression semantics.
- Execution progression must evolve from simple integer incrementing to explicit next-step selection.
- Testing and visualization become more involved.

### Option C — Condition/branch node as a first-class workflow node

Represent actions and decision points as different workflow nodes in a graph.

Conceptually:

```text
Step A -> Decision X -> Step B
                    -> Step C
```

**Advantages**

- Explicit graph model.
- Can support complex routing, joins, and future workflow-control constructs.

**Trade-offs**

- Significantly larger domain model than the current Phase 3 needs.
- Introduces node types, graph rules, and execution semantics before concrete requirements justify them.
- Higher implementation and testing cost.

## 5. Important Consequence

The choice is not isolated to `Workflow`.

If branching is introduced, the current `Execution.current_step: int` model cannot fully represent arbitrary non-linear progression. The existing `Execution.complete_step()` behavior assumes that the next step is always the next item in the list.

Therefore, silently adding a `condition` field to `WorkflowStep` would risk creating a domain model that says branching exists while the runtime model still assumes linear execution.

## 6. Recommendation for Decision

For a general automation platform, **Option B — explicit transition/edge concept** is the most coherent model to evaluate first because it keeps the distinction between work and routing explicit.

However, this is a material architecture decision. It should not be committed automatically merely because it is the recommended direction.

## 7. Proposed Minimal Scope If Option B Is Chosen

Keep the first implementation intentionally narrow:

- `WorkflowStep` remains an action definition.
- A transition identifies a source step and destination step.
- A transition may be unconditional or conditional.
- A condition is evaluated against runtime execution context.
- Execution selects a valid next transition after a step completes.
- No loops, parallel branches, joins, nested workflows, or event triggers are introduced in the first slice unless separately required.
- Existing retry semantics remain step-oriented; routing happens only after successful step completion.

## 8. Open Questions

1. Should every step have an explicit outgoing transition, or should the existing list order remain the default path?
2. What is the minimum condition language: fixed predicates, named condition objects, or an expression language?
3. Which layer evaluates conditions: domain object, domain service, or application service?
4. What happens when no transition matches?
5. What happens when multiple transitions match?
6. Are unconditional transitions required for ordinary linear workflows?
7. Are loops explicitly allowed in the first branching slice?
8. How should a workflow be validated for unreachable steps or dead ends?

## 9. Current Decision Status

**Not committed yet.**

No branching implementation should begin until the Project Owner confirms the routing model and the minimum condition semantics.

## Related Documentation

- `docs/02-Architecture/WORKFLOW_DESIGN_GATE.md`
- `docs/04-DECISIONS/ADR-005-Execution-Owns-Step-Progression.md`
- `docs/04-DECISIONS/ADR-004-Execution-and-Step-Retry-Semantics.md`
- `docs/04-DECISIONS/ADR-006-Capability-Result-and-Execution-Context-Flow.md`
