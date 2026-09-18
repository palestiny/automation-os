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

## Open Questions

- Whether step ordering should remain implicit list order or become an explicit domain concept.
- Whether capability identifiers should become a dedicated value object.
- Whether conditions belong directly to WorkflowStep or require a separate domain concept.
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

The next implementation increment should focus on strengthening the existing Workflow/WorkflowStep domain contract with tests, rather than introducing a large builder or infrastructure layer.

## Gate Result

The Phase 3 Workflow Engine boundary is sufficiently defined to begin a focused TDD increment.