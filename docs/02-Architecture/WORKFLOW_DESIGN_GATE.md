# Workflow Engine — Design Gate

- Status: Core definition, construction, and routing boundaries implemented; Phase 3 remains in progress
- Phase: Phase 3 — Workflow Engine
- Scope: Workflow domain definition, construction, and boundary
- Owner: Khaled (Project Owner / Decision Maker / Tech Lead)

## Purpose

Define the business meaning and ownership boundary of `Workflow` before implementing the next Phase 3 behavior.

This document is a design gate, not an implementation specification. It records the current understanding, committed decisions, trade-offs, assumptions, and open questions so implementation does not silently redefine the domain.

## 1. Concept

A `Workflow` is a reusable business-process definition describing an ordered set of steps and explicit routing between those steps.

A Workflow is a **definition**, not a runtime execution.

An `Execution` is a runtime instance of a Workflow and owns runtime state, current-step progression, retry lifecycle, and execution context.

Current implementation reflects this separation:

- `Workflow` contains definition-level steps, transitions, and publication state.
- `Execution` references the Workflow by `workflow_id` and creates runtime `ExecutionStep` objects from Workflow steps.
- `Execution` owns runtime progression after an explicit routing decision.

## 2. Business Meaning

The business meaning of a Workflow is:

> A named, reusable definition of how a business automation should proceed from one capability step to another.

The Workflow should answer questions such as:

- What steps belong to this automation?
- Which capability is associated with each step?
- Which transitions connect the steps?
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
- WorkflowStep definitions.
- Transition definitions.
- Workflow definition state/lifecycle.
- Structural validity of the workflow definition.
- Rules governing whether the definition can be modified or published.

### Workflow does not own

- Runtime execution state.
- Execution retries.
- Runtime step attempts.
- Execution context/output.
- Capability execution itself.
- Runtime condition evaluation.
- Job/progress tracking.

### Execution owns

- Runtime lifecycle.
- Runtime ExecutionStep state.
- Current-step position.
- Applying the explicitly selected next step.
- Execution-level retry semantics.

### Orchestrator/application layer owns

- Capability dispatch coordination.
- Runtime condition evaluation.
- Transition eligibility and selection.
- Passing the selected target to Execution.

This is consistent with ADR-005 and ADR-011.

## 4. WorkflowStep Boundary

`WorkflowStep` is part of the Workflow definition.

It describes a step that should be performed, including at minimum:

- step identity
- step name
- capability reference

It does not own runtime state such as `RUNNING`, `FAILED`, or attempt count. Runtime state belongs to `ExecutionStep`.

## 5. Transition Boundary

`Transition` is a definition-level routing concept.

It identifies:

- source step
- target step
- optional named condition reference

A transition may be unconditional or conditional. The Workflow stores the condition reference but does not execute or interpret it.

The first condition implementation uses an in-memory `ConditionRegistry`. The registry evaluates a named condition against `ExecutionContext`; the Orchestrator uses the result to select exactly one eligible transition.

Workflow graph validation treats conditional transitions as structural edges. It does not evaluate their runtime conditions.

## 6. Relationship to Execution

The intended conceptual relationship is:

```text
Workflow (definition)
    |
    +-- WorkflowStep (definition)
    +-- Transition (definition)
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

The current implementation creates an Execution from a Workflow and creates runtime ExecutionStep objects from the Workflow's steps. Runtime routing is selected by the application/orchestrator and applied by Execution.

## 7. Committed Design Decisions

### Decision A — Published Workflow is immutable

Once published, the Workflow definition cannot be changed. A changed definition will require a new Workflow revision/version when that product capability is introduced.

**Why**

- Protects runtime reproducibility.
- Prevents the meaning of a published definition from changing unexpectedly.
- Keeps the Execution/Workflow boundary predictable.
- Avoids introducing a versioning model before the product actually needs editing of published definitions.

**Status:** Committed and recorded in `ADR-009-Workflow-Definition-Immutability.md`.

### Decision B — Execution Workflow identification remains unchanged for now

Phase 3 will not introduce Workflow versioning solely to support future requirements.

The current Execution model stores `workflow_id` and materializes runtime `ExecutionStep` objects from the Workflow definition.

When published-definition revisions become a concrete requirement, the project will decide between Workflow versioning, a WorkflowRevision concept, or another explicit reproducibility mechanism.

**Status:** Deferred design decision.

### Decision C — Workflow owns definition structure

Workflow owns its steps, transitions, and structural validation. The application/orchestrator must not redefine the Workflow's definition structure during execution.

**Status:** Committed.

### Decision D — Workflow lifecycle remains intentionally small

For Phase 3 the lifecycle remains:

```text
DRAFT -> PUBLISHED
```

A Workflow cannot be published twice, an empty Workflow cannot be published, and published Workflows cannot be modified through domain operations.

States such as `ARCHIVED` or `DISABLED` are deferred until a concrete business requirement exists.

**Status:** Committed for current Phase 3 scope.

### Decision E — WorkflowBuilder is a construction API, not a runtime service

`WorkflowBuilder` exists to make construction of a Workflow definition explicit and readable. It collects the definition inputs and produces a `Workflow` in `DRAFT` state.

The builder:

- accepts the Workflow name;
- adds ordered WorkflowStep definitions;
- delegates step-level validity to `WorkflowStep.create()`;
- delegates Workflow-level creation/invariants to `Workflow.create()`;
- creates explicit unconditional transitions for its linear step sequence;
- does not resolve capabilities;
- does not execute capabilities;
- does not publish the Workflow automatically;
- does not own runtime state.

`build()` currently requires a name and at least one step. This keeps a built Workflow immediately meaningful while leaving the domain aggregate capable of representing an empty draft when needed for direct domain construction.

**Trade-off:** keeping the builder minimal avoids premature support for advanced configuration, conditions, branches, or triggers. The cost is that those future concerns will require deliberate API evolution rather than being predicted now.

**Status:** Committed for the current Phase 3 slice.

## 8. Workflow Definition Validity

The Workflow domain protects invariants that are intrinsic to the definition itself. It does not reach into external systems merely to validate dependencies.

### Implemented baseline invariants

- Workflow name must not be blank.
- A Workflow must contain at least one step before publication.
- WorkflowStep name must not be blank.
- WorkflowStep capability reference must not be blank.
- Step order is represented by collection order; no separate ordering field is required.
- Duplicate capability references are allowed. The same capability may legitimately appear more than once in a workflow.
- Workflow publication does not require resolving whether the referenced capability is currently registered. Capability availability is an application/runtime concern, not a basic Workflow-definition invariant.
- Transition source and target must belong to the Workflow.
- Transition cannot point to itself.
- Graph validation can reject WorkflowSteps that are unreachable from the first WorkflowStep.

### Explicitly deferred validation

- Capability registry existence/availability.
- Runtime condition satisfiability.
- Mutual exclusivity of conditions.
- Loop/cycle policy.
- Guaranteed terminal reachability.
- Trigger/event validity.
- External provider configuration.
- Runtime dependency checks.

These rules belong to later design gates unless the domain meaning changes.

**Status:** Implemented for the current Phase 3 slice, with additional graph rules deliberately deferred.

## 9. Encapsulation of Published Definitions

The Workflow definition is encapsulated behind read-only properties for identity, name, state, steps, and transitions.

Mutation remains possible only through explicit domain operations such as `publish()`, `add_step()`, and `add_transition()`, which enforce lifecycle rules.

**Status:** Implemented and recorded in ADR-009.

## 10. Current Assumptions

- A Workflow can be reused by multiple Executions.
- A published Workflow represents a stable executable definition.
- WorkflowStep order is meaningful and identifies the entry point as the first step.
- Capability execution is outside Workflow's responsibility.
- Execution remains the authoritative runtime owner.
- A conditional transition represents a structural edge regardless of its runtime evaluation result.
- Versioning may become necessary when published Workflow editing is introduced, but is not assumed to be required for every Phase 3 feature.

## 11. Open Questions

1. When published-definition editing becomes a requirement, should version belong to Workflow itself or to a separate WorkflowRevision concept?
2. What metadata is required for a Workflow beyond name and steps?
3. When should capability configuration become part of WorkflowStep, and what shape should that configuration take?
4. How should concrete trigger adapters resolve a workflow_id to a published Workflow, and should trigger payloads be propagated into ExecutionContext?
5. Should graph validation become a mandatory publication invariant once the construction lifecycle is mature enough to guarantee complete transition materialization?
6. What loop/cycle policy is required if workflows eventually need intentional loops?

## 12. Committed So Far

- Workflow is a definition, not a runtime execution.
- WorkflowStep is definition-level; ExecutionStep is runtime-level.
- Execution owns runtime step progression.
- Orchestrator coordinates capability execution and routing decisions.
- Workflow must not directly execute capabilities.
- Published Workflow definitions are immutable.
- Workflow owns definition structure and structural validation.
- Phase 3 keeps the Workflow lifecycle intentionally small.
- Phase 3 does not introduce versioning prematurely.
- Workflow definition invariants are protected at the domain boundary.
- WorkflowBuilder is a minimal construction API and does not own runtime concerns.
- Explicit Transition routing is the definition-level routing model.
- Named conditions and the ConditionRegistry are the first condition-evaluation slice.
- Reachability is the first graph-validation invariant.
- Triggers produce WorkflowStartRequest and do not own Execution lifecycle.

## 13. Next Gate

The next substantive Phase 3 design boundary is whether additional graph invariants are required by a concrete workflow use case, particularly publication-time validation and loop policy.

The trigger boundary is now committed in `TRIGGER_DESIGN_GATE.md` and `ADR-012-Workflow-Start-Trigger-Boundary.md`. Concrete trigger adapters, Workflow resolution, payload propagation, and execution persistence remain deferred until business requirements are concrete.

## Related Documentation

- `PROJECT_CONSTITUTION.md`
- `KHALED_ENGINEERING_WORKING_RULES.md`
- `docs/01-Roadmap/ROADMAP.md`
- `docs/02-Architecture/CONDITIONS_DESIGN_GATE.md`
- `docs/02-Architecture/CONDITION_SEMANTICS_DESIGN.md`
- `docs/02-Architecture/WORKFLOW_GRAPH_VALIDATION_DESIGN.md`
- `docs/04-DECISIONS/ADR-005-Execution-Owns-Step-Progression.md`
- `docs/04-DECISIONS/ADR-004-Execution-and-Step-Retry-Semantics.md`
- `docs/04-DECISIONS/ADR-009-Workflow-Definition-Immutability.md`
- `docs/04-DECISIONS/ADR-011-Workflow-Transition-Routing.md`
