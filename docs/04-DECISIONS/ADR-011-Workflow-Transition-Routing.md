# ADR-011 — Workflow Transition-Based Routing

- Status: Accepted
- Phase: Phase 3 — Workflow Engine
- Date: 2026-09-16

## Context

The Workflow model currently represents an ordered collection of steps, while Execution progresses through that collection using an integer `current_step`.

That model is sufficient for linear workflows but does not represent multiple possible destinations from a step. Attaching conditions directly to `WorkflowStep` would blur the distinction between work and routing and would not provide a clean representation of multiple destinations.

## Decision

Workflow routing will use an explicit **Transition** concept.

A Transition represents movement from a source `WorkflowStep` to a destination `WorkflowStep` and may carry routing criteria.

Conceptually:

```text
Step A --[condition X]--> Step B
       --[condition !X]--> Step C
```

`WorkflowStep` remains responsible for describing work. Transition is responsible for describing routing.

For workflows created through `WorkflowBuilder`, linear step sequences are materialized as explicit unconditional transitions between adjacent steps. Therefore, published workflows do not rely on an implicit runtime fallback from one list position to the next.

A single-step workflow has no transition because there is no next step.

Execution remains the authoritative owner of runtime progression. The Orchestrator/application layer coordinates condition evaluation and routing without becoming a second lifecycle owner.

## Condition Evaluation Decision

The first branching slice uses a named condition reference rather than an embedded expression language.

The concrete evaluator mechanism is an in-memory **ConditionRegistry** that maps a normalized condition name to a callable receiving `ExecutionContext` and returning `bool`.

The registry owns condition lookup and invocation only. It does not select transitions, mutate `Execution`, or own workflow runtime state.

This choice keeps the first implementation small and testable while preserving a replaceable evaluator boundary.

Persistence, dynamic/user-authored condition definitions, condition versioning, expression languages, and condition composition are deferred until concrete requirements exist.

## Consequences

### Positive

- Separates work definition from routing semantics.
- Supports multiple destinations from a step.
- Gives conditions a natural ownership boundary.
- Provides a foundation for future workflow graph behavior without making `WorkflowStep` responsible for it.
- Keeps runtime routing explicit and avoids two competing routing models.
- Preserves convenient linear workflow construction through the Builder.
- Keeps condition evaluation replaceable and separate from runtime progression.

### Negative

- Adds a domain concept and structural validation.
- Requires explicit runtime next-step selection for branching.
- The existing `current_step` integer remains an execution cursor into the runtime-step snapshot; it is not a routing mechanism. Explicit Transition target IDs determine branching destinations.
- Additional tests are required for routing, invalid graph definitions, and publication-time graph validation.
- The in-memory registry does not by itself provide persistence or user-authored condition configuration.

## Scope Constraints

This ADR does not introduce:

- parallel execution;
- joins;
- nested workflows;
- concrete event-trigger adapters;
- a general-purpose graph engine;
- a general expression language;
- persisted or dynamically authored condition definitions.

Those require separate design decisions when concrete requirements exist.

## Deferred Decisions

The following remain open:

- loop policy;
- additional graph validation rules beyond the currently committed reachability invariant;
- richer workflow construction APIs for branching;
- whether registry failures should become dedicated application error types;
- persistence/versioning/dynamic configuration of condition definitions if later required.

Condition representation and the first evaluator mechanism are committed: the first branching slice uses a named condition reference backed by an in-memory ConditionRegistry, as documented in `CONDITION_SEMANTICS_DESIGN.md`.

## Related Documentation

- `docs/02-Architecture/WORKFLOW_DESIGN_GATE.md`
- `docs/02-Architecture/CONDITIONS_DESIGN_GATE.md`
- `docs/02-Architecture/CONDITION_SEMANTICS_DESIGN.md`
- `docs/04-DECISIONS/ADR-005-Execution-Owns-Step-Progression.md`
- `docs/04-DECISIONS/ADR-004-Execution-and-Step-Retry-Semantics.md`
