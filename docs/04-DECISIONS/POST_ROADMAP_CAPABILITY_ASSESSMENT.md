# Automation OS — Post-Roadmap Capability Assessment

## Status
**Analysis only — no capability selected or committed.**

This document prepares the next Project Owner decision after completion of the committed post-Phase-7 capability sequence.
It does **not** authorize implementation.

## 1. Verified Baseline

The current platform already establishes:
- deterministic intent and workflow selection;
- workflow composition and validation;
- human decision boundaries;
- scheduling/triggers and external event integration;
- provider-independent capability execution;
- durable persistence;
- execution recovery;
- immutable workflow versions;
- operational metrics;
- AI planning;
- workflow generation with explicit DRAFT → review/publish boundaries;
- marketplace foundations;
- multi-tenant / authorization boundaries;
- workflow-start idempotency and replay semantics.

The current repository has:
- `master` as the only branch;
- 0 open pull requests;
- no open GitHub issues found during this assessment;
- latest verified master CI run #1850 successful.

## 2. Actual Product/Architecture Gaps

The remaining gaps are not failures in the current runtime. They are capability opportunities around the platform's mature flow:

`Intent → Understand → Select/Plan → Compose → Validate → Trigger → Execute → Observe → Recover → Improve`

The current implementation is strongest at the **workflow/runtime platform layer**. The main uncommitted opportunities are therefore around making that platform easier to operate, integrate, distribute, and improve.

## 3. Candidate A — Human Workflow Review / Operations Surface

### Problem
Workflow generation can persist DRAFT workflows and the application boundary can retrieve them for review, but the repository intentionally stops short of a product-level review/operations surface.

### Potential scope
- reviewer queue;
- workflow draft inspection;
- validation/error presentation;
- explicit approve/reject actions;
- publication audit evidence;
- execution inspection;
- tenant-aware operational views.

### Dependencies
Already established: generated DRAFT persistence; explicit publication boundary; authorization/tenant boundaries; execution history; observability.

### Main trade-off
**API/application-first:** reusable and avoids premature UI coupling.

**Full operations UI:** immediate usability but introduces frontend/product scope and a new delivery surface.

### Risk
Low architectural risk if kept as an application/API boundary first.

## 4. Candidate B — Credential / Secret / Provider Configuration Boundary

### Problem
The platform has capability/provider boundaries, but production automation eventually needs controlled external-provider configuration without leaking credentials into workflows, intents, or AI-generated artifacts.

### Potential scope
- provider connection identity;
- secret reference rather than secret value in workflows;
- credential ownership and tenant isolation;
- provider configuration validation;
- execution-time credential resolution;
- rotation/revocation semantics.

### Dependencies
Capability/provider boundary; multi-tenant authorization; durable persistence; execution lifecycle.

### Main trade-off
**Minimal credential-reference boundary:** establishes safe ownership and indirection first.

**Full secrets-management subsystem:** stronger operational model but adds substantial infrastructure/security complexity.

### Risk
High security sensitivity. This capability requires a dedicated Design Gate before implementation.

## 5. Candidate C — Durable Event / Notification Infrastructure

### Problem
External event integration and operational metrics exist, but a broader durable event/notification mechanism is intentionally not part of the current committed architecture.

### Potential scope
- durable domain/application event publication;
- delivery guarantees;
- webhook/event subscriptions;
- notifications;
- retry/dead-letter semantics;
- correlation with executions.

### Dependencies
Durable persistence; execution/history evidence; external event boundaries; recovery/idempotency contracts.

### Main trade-off
**Targeted event delivery:** solves a concrete integration need without introducing a generic bus.

**Generic event bus:** broad extensibility, but substantially increases infrastructure and consistency complexity.

### Risk
Medium/high. Project rules explicitly avoid generic event-bus infrastructure without a concrete requirement.

## 6. Candidate D — Workflow Productization / Reuse Layer

### Problem
The platform can build, version, publish, discover, install, and generate workflows, but a mature ecosystem may need stronger reuse semantics around templates, configuration, compatibility, and lifecycle.

### Potential scope
- reusable workflow templates;
- parameterized workflow products;
- compatibility metadata;
- version compatibility rules;
- template cloning/customization;
- controlled promotion between environments/tenants.

### Dependencies
WorkflowVersion; marketplace; workflow generation; multi-tenancy; validation.

### Main trade-off
**Template/reuse layer:** increases value of existing workflow artifacts without changing execution semantics.

**Environment/release model:** more powerful but introduces deployment, promotion, rollback, and compatibility concerns.

### Risk
Medium. Must avoid turning marketplace/workflow versioning into an implicit deployment system.

## 7. Candidate Comparison

| Candidate | Primary value | Existing dependency coverage | Architectural risk | New infrastructure pressure |
|---|---|---:|---:|---:|
| Human Review / Operations | Makes current generation/runtime capabilities operable | High | Low–Medium | Low–Medium |
| Credential / Provider Configuration | Enables safer real-world provider usage | Medium–High | High | Medium–High |
| Durable Events / Notifications | Expands integrations and operational reactions | High | Medium–High | High |
| Workflow Productization / Reuse | Increases reuse/distribution value | High | Medium | Medium |

This table is a comparison, not a selection.

## 8. Assessment Result

No candidate is automatically activated.

The repository evidence suggests that the next Design Gate should be driven by the product bottleneck the Project Owner wants to solve:

- If the immediate goal is **making existing capabilities usable by operators**, investigate Human Review / Operations.
- If the immediate goal is **connecting real external providers safely**, investigate Credential / Provider Configuration.
- If the immediate goal is **reactive integration and notifications**, investigate Durable Events / Notifications.
- If the immediate goal is **turning workflows into reusable/distributable products**, investigate Workflow Productization / Reuse.

These are distinct product directions and should not be combined into one oversized capability.

## 9. Required Next Decision

Before implementation, the Project Owner must select **one problem**, not merely one technology.

The selected problem then requires a normal Design Gate covering:

`UNDERSTAND → MAP → DESIGN → TRADE-OFFS → DECIDE → RED → GREEN → VERIFY → DOCUMENT → EXIT REVIEW`

Until that decision exists, safe maintenance and verification remain the active repository mode.

## 10. Explicit Non-Commitments

This assessment does not commit to:
- a frontend framework;
- a secrets provider;
- a message broker;
- a generic event bus;
- distributed microservices;
- autonomous AI execution;
- a deployment/release platform;
- a specific marketplace business model.

Those remain future decisions.