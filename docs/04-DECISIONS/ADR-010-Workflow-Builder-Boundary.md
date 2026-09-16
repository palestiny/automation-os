# ADR-010 — Workflow Builder Boundary

- Status: Accepted
- Phase: Phase 3 — Workflow Engine
- Date: 2026-09-16

## Context

The Workflow domain now protects its definition invariants, but callers need a clear construction API for assembling a workflow from a name and ordered capability steps.

The construction API must not become a second owner of Workflow business rules or runtime execution behavior.

## Decision

Introduce a minimal `WorkflowBuilder` in the application layer as a construction API.

The builder:

- accepts a Workflow name;
- adds ordered `WorkflowStep` definitions;
- delegates step validation to `WorkflowStep.create()`;
- delegates Workflow creation to `Workflow.create()`;
- returns a Workflow in `DRAFT` state;
- requires a name and at least one step when `build()` is called.

The builder does not:

- publish the Workflow automatically;
- resolve capabilities from the registry;
- execute capabilities;
- own runtime state;
- implement orchestration;
- introduce conditions, branches, triggers, or capability configuration.

## Rationale

The builder improves construction readability without moving domain ownership out of the Workflow aggregate.

Keeping it in the application layer also leaves the domain model focused on business invariants rather than fluent construction mechanics.

The builder's `build()` requirement for at least one step is a construction-level contract. The underlying Workflow aggregate may still represent an empty draft because direct domain construction and staged editing remain valid domain capabilities.

## Trade-offs

### Minimal builder

**Benefits**

- Small API surface.
- Easy to test.
- Avoids predicting future Workflow features.
- Keeps runtime concerns outside construction.

**Costs**

- Future configuration or branching requirements may require explicit API evolution.
- Some callers may eventually need a different construction path if workflows become more complex.

### Rich builder with future features now

Would reduce some future API changes, but would introduce abstractions and business concepts before their requirements are established. That would increase coupling and make the current Workflow boundary harder to reason about.

## Consequences

- Workflow construction is explicit and readable.
- Workflow remains the authority for its own definition invariants.
- Capability availability remains an application/runtime concern.
- Conditions, events/triggers, and capability configuration remain separate future design gates.
