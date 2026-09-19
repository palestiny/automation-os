# Phase 8.1 Design Gate — Workflow Composition / Builder

Status: **APPROVED FOR IMPLEMENTATION — Project Owner selected ordered capability sequence**
Capability: **Workflow Composition / Builder**
Position: **1 of 13**

## Objective

Provide a first-class way to compose, validate, inspect, and persist executable workflows from explicit workflow steps without coupling workflow definition to a UI, AI provider, or execution adapter.

## Problem

The platform already has workflow selection, generation/validation boundaries, and execution. The next gap is a stable composition boundary that lets workflows be constructed deliberately rather than through implicit or ad-hoc assembly.

## Scope

### In scope
- explicit workflow composition model;
- ordered workflow steps;
- step identity and stable references;
- capability reference per step;
- step input contract/value;
- workflow-level validation;
- deterministic validation errors;
- builder/application boundary independent of HTTP/UI;
- controlled workflow snapshots suitable for later versioning;
- tests for valid and invalid composition.

### Out of scope
- conditions/branching;
- scheduling;
- human approval;
- durable database persistence;
- workflow version history;
- AI planning;
- marketplace publication changes;
- authorization/ownership.

Those are later ordered capabilities.

## Architectural constraints

1. Existing Workflow remains the domain concept representing executable workflow intent.
2. Execution remains responsible for lifecycle; the builder does not execute workflows.
3. Capabilities are referenced by stable capability identity/contract rather than provider-specific implementation details.
4. Validation is deterministic and side-effect free.
5. The composition API must be usable without HTTP or UI.
6. Persistence adapters are not redesigned here; the resulting workflow representation remains compatible with the existing repository boundary.

## Alternatives and trade-offs

### A — Dedicated Workflow Builder application service
Pros: explicit composition boundary; easy TDD; reusable by API, future UI, and AI planning.
Trade-off: introduces another application abstraction.

### B — Make Workflow itself a mutable builder
Pros: fewer classes.
Trade-off: mixes construction and domain lifecycle concerns; makes controlled snapshots harder; increases coupling to future versioning.

### Decision
**A — Dedicated Workflow Builder application boundary.**

The decision is limited to this capability and does not pre-commit later UI, persistence, or versioning architecture.

## TDD contract

RED tests must cover:
- create workflow with valid ordered steps;
- reject empty workflow;
- reject duplicate step identities;
- reject missing capability reference;
- reject invalid step input contract;
- preserve step order;
- produce deterministic validation errors;
- builder does not execute the workflow;
- resulting workflow can be consumed by existing execution boundaries.

## Exit criteria

- all RED tests are GREEN;
- full regression suite passes;
- no later capability is pulled into scope;
- Design Gate and exit review are updated;
- PROJECT_STATUS reflects completion;
- deferred scope is recorded.

## Next capability

After this capability is complete, activate capability 2 — Condition / Decision Engine with a separate Design Gate.