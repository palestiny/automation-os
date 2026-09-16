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

## Consequences

### Positive

- Separates work definition from routing semantics.
- Supports multiple destinations from a step.
- Gives conditions a natural ownership boundary.
- Provides a foundation for future workflow graph behavior without making `WorkflowStep` responsible for it.
- Keeps runtime routing explicit and avoids two competing routing models.
- Preserves convenient linear workflow construction through the Builder.

### Negative

- Adds a domain concept and structural validation.
- Requires explicit runtime next-step selection for branching.
- The existing `current_step` integer cannot remain the complete representation of runtime position for arbitrary branching.
- Additional tests are required for routing and invalid graph definitions.

## Scope Constraints

This ADR does not introduce:

- parallel execution;
- joins;
- nested workflows;
- event triggers;
- a general-purpose graph engine;
- a general expression language.

Those require separate design decisions when concrete requirements exist.

## Deferred Decisions

The following remain open:

- condition evaluator API and ownership;
- no-match behavior at runtime;
- multiple-match behavior at runtime;
- loop policy;
- graph validation rules beyond Transition endpoint ownership;
- richer workflow construction APIs for branching.

Condition representation is no longer deferred at the baseline level: the first branching slice uses a named condition reference, as documented in `CONDITION_SEMANTICS_DESIGN.md`.

## Related Documentation

- `docs/02-Architecture/WORKFLOW_DESIGN_GATE.md`
- `docs/02-Architecture/CONDITIONS_DESIGN_GATE.md`
- `docs/02-Architecture/CONDITION_SEMANTICS_DESIGN.md`
- `docs/04-DECISIONS/ADR-005-Execution-Owns-Step-Progression.md`
- `docs/04-DECISIONS/ADR-004-Execution-and-Step-Retry-Semantics.md`
