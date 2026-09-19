# Phase 8.1 Design Gate — Workflow Composition / Builder

Status: **APPROVED FOR IMPLEMENTATION — Project Owner selected ordered capability sequence**
Capability: **Workflow Composition / Builder**
Position: **1 of 13**

## Objective

Provide a first-class application boundary to compose and validate executable workflow definitions from explicit ordered workflow steps without coupling workflow construction to HTTP, UI, AI providers, or execution adapters.

## Problem

The platform already has workflow selection, generation/validation boundaries, and execution. The next gap is a stable composition boundary that lets workflows be constructed deliberately rather than through implicit or ad-hoc assembly.

## Scope

### In scope
- explicit workflow composition model;
- ordered workflow steps;
- stable step identity and duplicate-identity validation;
- capability reference per step;
- workflow-level validation through existing domain invariants;
- deterministic validation errors;
- builder/application boundary independent of HTTP/UI;
- resulting workflow representation remains suitable for later versioning.

### Explicit boundary for step inputs

The current WorkflowStep domain model represents step identity, name, capability reference, and optional condition. It does **not** yet define a separate step input contract/value model.

Therefore Phase 8.1 does not invent a parallel input-contract abstraction. Step input contracts are deferred to the capability contract/provider work where their semantics can be defined against actual capability interfaces.

### Out of scope
- conditions/branching as a new decision engine;
- scheduling;
- human approval;
- durable database persistence;
- workflow version history;
- AI planning;
- marketplace publication changes;
- authorization/ownership;
- a new step-input contract model.

Those remain later capabilities.

## Architectural constraints

1. Existing Workflow remains the domain concept representing executable workflow intent.
2. Execution remains responsible for lifecycle; the builder does not execute workflows.
3. Capabilities are referenced by their existing capability identity string; provider-specific implementation details remain outside this boundary.
4. Validation is deterministic and side-effect free.
5. The composition API is usable without HTTP or UI.
6. Persistence adapters are not redesigned here.
7. The builder must preserve existing Workflow and WorkflowStep domain invariants rather than duplicate them unnecessarily.

## Alternatives and trade-offs

### A — Dedicated Workflow Builder application service
Pros: explicit composition boundary; easy TDD; reusable by API, future UI, and AI planning.
Trade-off: introduces another application abstraction.

### B — Make Workflow itself a mutable builder
Pros: fewer classes.
Trade-off: mixes construction and domain lifecycle concerns; makes controlled snapshots harder; increases coupling to future versioning.

### Decision

**A — Dedicated Workflow Builder application boundary.**

The decision is limited to this capability and does not pre-commit later UI, persistence, capability-provider, or versioning architecture.

## TDD contract

RED/GREEN verification covers:
- create workflow with valid ordered steps;
- reject empty workflow;
- reject duplicate step identities;
- reject non-WorkflowStep values at the application boundary;
- preserve step order;
- preserve existing workflow metadata;
- surface deterministic domain validation errors;
- builder does not execute the workflow;
- resulting workflow remains a normal Workflow consumable by existing boundaries.

## Verification

The validating GitHub Actions run for the implementation commit completed successfully with **470 tests passed**.

## Exit criteria

- all focused tests are GREEN;
- full regression suite passes;
- no later capability is pulled into scope;
- Design Gate and exit review are updated;
- PROJECT_STATUS reflects completion;
- deferred scope is recorded.

## Next capability

After this capability is complete, activate capability 2 — Condition / Decision Engine with a separate Design Gate.
