# Workflow Engine — Design Gate

- Status: In Review
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

Current implementation already reflects this separation:

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

## 6. Candidate Design Decisions

### Decision A — Published Workflow mutability

#### Option 1 — Published Workflow is immutable

Once published, the Workflow definition cannot be changed. A changed definition requires a new version or a new Workflow revision.

**Trade-offs**

- Strong runtime reproducibility.
- Easier reasoning about an Execution after it starts.
- Avoids changing the meaning of an already published definition.
- Requires a versioning/revision strategy when editing published workflows is needed.

#### Option 2 — Published Workflow remains mutable

Published workflows may have their steps changed directly.

**Trade-offs**

- Simpler editing model initially.
- Avoids introducing versioning early.
- But an Execution may become associated with a definition that changes while it is running or being inspected later.
- Reproducibility and auditability become harder.

**Current recommendation:** Option 1 — immutable published definition, with versioning introduced when editing published workflows becomes a concrete requirement.

**Decision status:** Open — requires Tech Lead decision before implementation depends on it.

### Decision B — How Execution identifies its Workflow definition

#### Option 1 — Workflow ID only

Execution stores only the Workflow identifier.

**Trade-offs**

- Simple.
- But insufficient by itself if multiple revisions of a Workflow are later supported.

#### Option 2 — Workflow ID + version

Execution identifies the exact Workflow definition revision it was created from.

**Trade-offs**

- Strong reproducibility and auditability.
- Makes future versioning explicit.
- Adds versioning concepts before they are necessarily required by the current product.

#### Option 3 — Full Workflow snapshot inside Execution

Execution stores a complete copy of the definition used for the run.

**Trade-offs**

- Maximum runtime self-containment.
- Strong historical reproducibility.
- Duplicates definition data and complicates persistence/update semantics.

**Current recommendation:** Option 2 as the long-term model, but do not introduce versioning solely for Phase 3 unless the domain requires it. The existing `Execution` implementation currently stores `workflow_id` and materializes runtime steps, so this remains an open evolution point.

**Decision status:** Open.

### Decision C — Workflow owns step ordering

#### Option 1 — Workflow owns ordering

The ordered collection of WorkflowStep objects is part of the Workflow definition.

**Trade-offs**

- Keeps business flow definition in the domain.
- Makes Workflow validation explicit.
- Keeps Orchestrator from becoming the source of business ordering rules.

#### Option 2 — Application layer owns ordering

The application/orchestrator determines step order.

**Trade-offs**

- Can make Workflow smaller.
- But moves business meaning into orchestration code and risks multiple callers applying different ordering rules.

**Current recommendation:** Option 1.

**Decision status:** Proposed; consistent with the current model.

### Decision D — Workflow lifecycle

Current implementation has:

```text
DRAFT -> PUBLISHED
```

and prevents publishing an empty Workflow and adding steps after publication.

**Current recommendation:** Keep the lifecycle intentionally small for Phase 3. Do not add `ARCHIVED`, `DISABLED`, or other states until a concrete business requirement exists.

**Decision status:** Proposed.

## 7. Current Assumptions

- A Workflow can be reused by multiple Executions.
- A published Workflow represents a stable executable definition.
- WorkflowStep order is meaningful.
- Capability execution is outside Workflow's responsibility.
- Execution remains the authoritative runtime owner.
- Versioning may become necessary when published Workflow editing is introduced, but is not assumed to be required for every Phase 3 feature.

## 8. Open Questions

1. Do we need Workflow versioning in the current Phase 3 scope, or only when editing published definitions becomes a product requirement?
2. If versioning is introduced, should version belong to Workflow itself or to a separate WorkflowRevision concept?
3. What additional validation belongs inside Workflow before publication?
4. What metadata is required for a Workflow beyond name and steps?
5. Do future conditional branches belong inside WorkflowStep or require a separate domain concept?
6. How should triggers/events relate to Workflow without making Workflow responsible for external event infrastructure?

## 9. Committed So Far

- Workflow is a definition, not a runtime execution.
- WorkflowStep is definition-level; ExecutionStep is runtime-level.
- Execution owns runtime step progression.
- Orchestrator coordinates capability execution and delegates lifecycle transitions to Execution.
- Workflow must not directly execute capabilities.
- Phase 3 starts with domain/design clarification before adding behavior.

## 10. Next Gate

Before implementing the Workflow Builder or additional Workflow behavior:

1. Review this Design Gate against the current code and tests.
2. Resolve the open decisions that affect the implementation contract.
3. Record any architectural decision that becomes committed as an ADR.
4. Write behavior-first tests for the agreed Workflow rules.
5. Implement the smallest change that satisfies those tests.
6. Review, document, commit, push, and update project state.

## Related Documentation

- `PROJECT_CONSTITUTION.md`
- `KHALED_ENGINEERING_WORKING_RULES.md`
- `docs/01-Roadmap/ROADMAP.md`
- `docs/04-DECISIONS/ADR-005-Execution-Owns-Step-Progression.md`
- `docs/04-DECISIONS/ADR-004-Execution-and-Step-Retry-Semantics.md`
