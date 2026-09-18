# Phase 3 — Workflow Engine Design Gate

Status: Design baseline
Date: 2026-09-18
Issue: #17

## Purpose

Phase 3 defines the Workflow as the declarative description of work to be executed. It must remain separate from Execution, which represents runtime state and progress.

## Committed Decisions

### 1. Workflow owns definition, not runtime

Workflow is responsible for:
- identity and name;
- ordered workflow steps;
- draft/published lifecycle;
- structural invariants required for a valid workflow definition.

Workflow does not own:
- execution state;
- current step at runtime;
- retries;
- scheduling;
- persistence mechanics;
- provider-specific execution.

### 2. WorkflowStep is a definition element

A WorkflowStep represents one ordered unit in a workflow definition.

Its current committed fields are:
- id;
- name;
- capability identifier.

The capability identifier remains provider-neutral. A step does not instantiate or execute a provider.

### 3. Published workflows are immutable

Once published, a Workflow definition cannot be modified through its current domain API. Draft workflows may be edited.

This protects the meaning of an existing Execution: an Execution references a Workflow definition that must not silently change underneath it.

Versioning is deferred until the repository demonstrates a concrete need for multiple published revisions of the same logical workflow.

### 4. Validation is layered

Workflow-domain validation owns structural rules that can be checked without external systems, such as:
- a publishable workflow must contain at least one step;
- steps cannot be added after publication;
- required step fields must be valid at the domain boundary.

Capability existence/availability is not a Workflow domain responsibility. That belongs to an application/capability boundary.

### 5. Builder is an authoring convenience

A Workflow Builder, when introduced, will simplify construction of valid draft workflows. It must not become a second domain model or bypass Workflow invariants.

The Workflow entity remains the authority for lifecycle and invariants.

### 6. Step ordering is collection order

Workflow step ordering is represented by the order of Workflow.steps.

No explicit position/index field is part of WorkflowStep.

Appending a step to a draft Workflow adds it to the end of the definition. Published workflows cannot be reordered because they cannot be modified.

This keeps the domain model small while the current execution model treats a Workflow definition as an ordered sequence. If future requirements need insertion, reordering, branching, or graph semantics, that will require a new design decision rather than silently adding ordering metadata.

### 7. Conditions are step-level declarative constraints

A condition belongs conceptually to a WorkflowStep because it determines whether that step is eligible to execute within the workflow definition.

The condition is a separate domain concept rather than an unstructured field on WorkflowStep. This keeps conditional semantics explicit and leaves room for domain invariants without coupling WorkflowStep to an expression language.

Workflow/WorkflowStep remain declarative: they store the condition definition but do not evaluate it. Evaluation belongs to the application/runtime boundary because it depends on execution context and an evaluation strategy.

No provider-specific expression language, evaluator implementation, or runtime context contract is introduced by this decision. Those require a concrete use case and a separate implementation/design decision.

### 8. Persistence is repository-based and aggregate-aligned

The first persistence strategy will preserve the existing domain boundaries rather than introducing database concerns into domain entities.

- Workflow definitions and Execution runtime state are persisted through separate repository responsibilities because they have different lifecycles and consistency boundaries.
- Repository contracts belong at the domain/application boundary; infrastructure owns the concrete database/ORM implementation.
- Persistence models may differ from domain objects. Repositories are responsible for mapping persisted data to and from valid domain aggregates rather than making the database schema the domain model.
- The first durable Execution record includes the aggregate lifecycle data already defined by the domain: execution id, workflow id, current step, state, attempt, and lifecycle timestamps.
- ExecutionContext is not automatically made durable by this decision. Durable WAITING/resume semantics may require persisted context, but its serialization and ownership contract need a concrete use case before implementation.
- No database vendor, ORM, scheduling mechanism, or background worker is selected by this strategy.

This keeps persistence replaceable while making aggregate durability explicit. A concrete infrastructure implementation can be introduced once a runtime use case requires process-restart durability.

## Open Questions

- Whether published workflow versioning becomes necessary once persistence/use cases are implemented.

## Deferred Scope

The following remain separate roadmap items:
- conditions;
- events/triggers;
- execution persistence strategy;
- external capability validation;
- plugin/provider implementation.

They must not be pulled into the basic Workflow definition contract without a new design decision.

## Design Consequence

The current Workflow model remains a small ordered definition. The capability identifier question is resolved without introducing a new abstraction. Further Phase 3 work should focus on conditions, events/triggers, or execution persistence only when their domain contracts are sufficiently understood.

## Gate Result

The Phase 3 Workflow Engine boundary is sufficiently defined to continue focused TDD increments.
