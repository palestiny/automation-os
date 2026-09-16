# ADR-009 — Workflow Definition Immutability

- Status: Accepted
- Phase: Phase 3 — Workflow Engine
- Date: 2026-09-16

## Context

A `Workflow` is a reusable definition of an automation, while an `Execution` is a runtime instance of that definition.

Published Workflow definitions must remain stable so that an Execution does not depend on a definition whose business meaning can change after publication.

The previous implementation prevented modification through `add_step()` after publication, but exposed mutable definition fields and a mutable steps collection. That allowed callers to bypass the domain rules directly.

## Decision

A published Workflow definition is immutable through the domain model.

The Workflow therefore owns and protects:

- identity
- name
- ordered WorkflowStep collection
- publication state

The public API exposes these values as read-only properties. Definition mutation is performed only through explicit domain operations such as `add_step()`, and those operations enforce the Workflow lifecycle rules.

The Workflow lifecycle remains:

```text
DRAFT -> PUBLISHED
```

Once published:

- steps cannot be added through domain operations;
- the definition cannot be changed through exposed mutable collections;
- definition fields are not publicly assignable.

Changing a published definition will require a future revision/version model. That model is intentionally deferred until published-definition editing becomes a concrete product requirement.

## Consequences

### Positive

- Protects reproducibility of Executions.
- Keeps Workflow responsible for its own invariants.
- Prevents accidental mutation through ordinary Python object access.
- Keeps versioning out of Phase 3 until it has a concrete business need.

### Trade-offs

- The Workflow API is more encapsulated than a plain mutable dataclass.
- Callers cannot mutate the steps collection directly; they must use domain operations.
- Future editing of published definitions requires an explicit version/revision design.

## Alternatives Considered

### Mutable published Workflow

Simpler initially, but allows the meaning of a definition to change after it has been published. This weakens reproducibility and makes runtime behavior harder to reason about.

### Public mutable list with convention

Keeps the current API shape but does not enforce the domain invariant. Python callers can bypass `add_step()` and mutate the collection directly.

### Versioning immediately

Would provide explicit historical identity for definitions, but introduces a version/revision model before the product currently requires editing published definitions.

## Related Decisions

- `ADR-005-Execution-Owns-Step-Progression.md`
- `ADR-004-Execution-and-Step-Retry-Semantics.md`
- `WORKFLOW_DESIGN_GATE.md`
