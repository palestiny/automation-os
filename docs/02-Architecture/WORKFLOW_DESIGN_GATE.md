# Workflow Engine — Design Gate

- Status: Core definition gate implemented; Phase 3 remains in progress
- Phase: Phase 3 — Workflow Engine
- Scope: Workflow domain definition and boundary
- Owner: Khaled (Project Owner / Decision Maker / Tech Lead)

## Purpose

Define the business meaning and ownership boundary of `Workflow` before implementing the next Phase 3 behavior.

This document is a design gate, not an implementation specification. It records the current understanding, candidate decisions, trade-offs, assumptions, and open questions so implementation does not silently redefine the domain.

## 1. Concept

A `Workflow` is a reusable business-process definition describing an ordered set of steps that can be executed.

A Workflow is a **definition**, not a runtime execution.

An `Execution` is a runtime instance of a Workflow and owns runtime state, current-step progression, retry lifecycle, and execution context.

Current implementation reflects this separation:

- `Workflow` contains definition-level steps and publication state.
- `Execution` references the Workflow by `workflow_id` and creates runtime `ExecutionStep` objects from Workflow steps.
- `Execution` owns runtime progression through `current_step`.

## 2. Business Meaning

The business meaning of a Workflow is:

> A named, reusable definition of how a business automation should proceed from one capability step to another.

The Workflow should answer questions such as:

- What steps belong to this automation?
- In what order are those steps defined?
- Which capability is associated with each step?
- Is the definition currently editable or published?

The Workflow should not answer runtime questions such as:

- Which execution is currently running?
- How many times has a step been retried during a particular execution?
- What output was produced by a capability during a particular execution?
- Whether a particular execution is waiting, failed, or cancelled.

Those belong to the execution/runtime model.

## 3. Ownership Boundary

### Workflow owns

- Workflow identity.
- Workflow name/metadata required by the domain.
- Ordered WorkflowStep definition.
- Workflow definition state/lifecycle.
- Rules that protect the validity of the workflow definition.
- Rules governing whether the definition can be modified or published.

### Workflow does not own

- Runtime execution state.
- Execution retries.
- Runtime step attempts.
- Execution context/output.
- Capability execution itself.
- Job/progress tracking.

### Execution owns

- Runtime lifecycle.
- Runtime ExecutionStep state.
- Current-step position.
- Step progression.
- Execution-level retry semantics.

This is consistent with ADR-005: Execution owns workflow step progression.

## 4. WorkflowStep Boundary

`WorkflowStep` is part of the Workflow definition.

It describes a step that should be performed, including at minimum:

- step identity
- step name
- capability reference

It does not own runtime state such as `RUNNING`, `FAILED`, or attempt count. Runtime state belongs to `ExecutionStep`.

## 5. Relationship to Execution

The intended conceptual relationship is:

```text
Workflow (definition)
    |
    +-- WorkflowStep (definition)
    |
    v
Execution (runtime instance)
    |
    +-- ExecutionStep (runtime state)
    +-- ExecutionContext (runtime data)
    |
    v
Capability execution
```

The current implementation creates an Execution from a Workflow and creates runtime ExecutionStep objects from the Workflow's steps. This preserves a clean definition/runtime boundary.

## 6. Committed Design Decisions

### Decision A — Published Workflow is immutable

Once published, the Workflow definition cannot be changed. A changed definition will require a new Workflow revision/version when that product capability is introduced.

**Why**

- Protects runtime reproducibility.
- Prevents the meaning of a published definition from changing unexpectedly.
- Keeps the Execution/Workflow boundary predictable.
- Avoids introducing a versioning model before the product actually needs editing of published definitions.

**Deferred consequence**

Published-definition editing is not supported by the current Phase 3 model. If editing becomes a requirement, version/revision semantics must be designed before implementation.

**Status:** Committed and recorded in `ADR-009-Workflow-Definition-Immutability.md`.

### Decision B — Execution Workflow identification remains unchanged for now

Phase 3 will not introduce Workflow versioning solely to support future requirements.

The current Execution model stores `workflow_id` and materializes runtime `ExecutionStep` objects from the Workflow definition.

When published-definition revisions become a concrete requirement, the project will decide between Workflow versioning, a WorkflowRevision concept, or another explicit reproducibility mechanism.

**Status:** Deferred design decision.

### Decision C — Workflow owns step ordering

The ordered WorkflowStep collection is part of the Workflow definition. The order in the Workflow is the business-defined execution order.

The application/orchestrator must not independently redefine that ordering.

**Status:** Committed.

### Decision D — Workflow lifecycle remains intentionally small

For Phase 3 the lifecycle remains:

```text
DRAFT -> PUBLISHED
```

A Workflow cannot be published twice, an empty Workflow cannot be published, and published Workflows cannot be modified through domain operations.

States such as `ARCHIVED` or `DISABLED` are deferred until a concrete business requirement exists.

**Status:** Committed for current Phase 3 scope.

## 7. Workflow Definition Validity

The Workflow domain protects invariants that are intrinsic to the definition itself. It does not reach into external systems merely to validate dependencies.

### Implemented baseline invariants

- Workflow name must not be blank.
- A Workflow must contain at least one step before publication.
- WorkflowStep name must not be blank.
- WorkflowStep capability reference must not be blank.
- Step order is represented by collection order; no separate ordering field is required.
- Duplicate capability references are allowed. The same capability may legitimately appear more than once in a workflow.
- Workflow publication does not require resolving whether the referenced capability is currently registered. Capability availability is an application/runtime concern, not a basic Workflow-definition invariant.

### Explicitly deferred validation

- Capability registry existence/availability.
- Conditional branch validity.
- Trigger/event validity.
- External provider configuration.
- Runtime dependency checks.

These rules belong to later design gates unless the domain meaning changes.

**Status:** Implemented for the current Phase 3 slice.

## 8. Encapsulation of Published Definitions

The Workflow definition is now encapsulated behind read-only properties for identity, name, state, and the ordered steps collection.

Mutation remains possible only through explicit domain operations such as `publish()` and `add_step()`, which enforce lifecycle rules.

This closes the previous invariant gap where callers could bypass `add_step()` by mutating the public list directly.

**Status:** Implemented and recorded in ADR-009.

## 9. Current Assumptions

- A Workflow can be reused by multiple Executions.
- A published Workflow represents a stable executable definition.
- WorkflowStep order is meaningful.
- Capability execution is outside Workflow's responsibility.
- Execution remains the authoritative runtime owner.
- Versioning may become necessary when published Workflow editing is introduced, but is not assumed to be required for every Phase 3 feature.

## 10. Open Questions

1. When published-definition editing becomes a requirement, should version belong to Workflow itself or to a separate WorkflowRevision concept?
2. What metadata is required for a Workflow beyond name and steps?
3. Do future conditional branches belong inside WorkflowStep or require a separate domain concept?
4. How should triggers/events relate to Workflow without making Workflow responsible for external event infrastructure?
5. When should capability configuration become part of WorkflowStep, and what shape should that configuration take?

## 11. Committed So Far

- Workflow is a definition, not a runtime execution.
- WorkflowStep is definition-level; ExecutionStep is runtime-level.
- Execution owns runtime step progression.
- Orchestrator coordinates capability execution and delegates lifecycle transitions to Execution.
- Workflow must not directly execute capabilities.
- Published Workflow definitions are immutable.
- Workflow owns step ordering.
- Phase 3 keeps the Workflow lifecycle intentionally small.
- Phase 3 does not introduce versioning prematurely.
- Workflow definition invariants are protected at the domain boundary.

## 12. Next Gate

The next Phase 3 design gate is the Workflow Builder / definition-construction model. It should determine how workflows are assembled and validated without moving runtime concerns into the Workflow aggregate.

Before that implementation:

1. Review the current Workflow contract against the repository tests.
2. Run the full test suite locally and compare against the previous verified baseline of 79 passed.
3. Update roadmap/project state after the local test result is known.
4. Commit and push the completed slice.

## Related Documentation

- `PROJECT_CONSTITUTION.md`
- `KHALED_ENGINEERING_WORKING_RULES.md`
- `docs/01-Roadmap/ROADMAP.md`
- `docs/04-DECISIONS/ADR-005-Execution-Owns-Step-Progression.md`
- `docs/04-DECISIONS/ADR-004-Execution-and-Step-Retry-Semantics.md`
- `docs/04-DECISIONS/ADR-009-Workflow-Definition-Immutability.md`
