# Multiple Automation Domains Design Gate

## Purpose

Expand Automation OS beyond Content Automation without coupling the platform core to any single business domain.

## Problem

Content Automation currently proves the platform runtime, but platform generalization requires a second domain to demonstrate that workflows, intents, capabilities, execution, and outcomes are reusable rather than content-specific abstractions.

## Committed Decisions

1. The existing Execution and Workflow engines remain domain-neutral.
2. A domain owns its business vocabulary and capabilities; it does not create a second execution engine.
3. Intent goals identify business intent but do not identify providers.
4. Domain-specific capabilities use the existing Capability contract.
5. Domain-specific workflows remain ordinary Workflow definitions.
6. Cross-domain orchestration uses existing application boundaries.
7. Content remains one domain, not the platform's base domain.
8. The first additional domain will be a lightweight **Business Reporting** domain.
9. The reporting domain will initially produce a report asset from structured business data.
10. No external SaaS/API provider is required for the first slice; deterministic in-memory data is sufficient.
11. No shared generic "BusinessEntity" model will be introduced merely to force reuse.
12. Domain boundaries are demonstrated through separate vocabulary and capabilities.
13. Provider integration remains deferred until the domain boundary is proven.

## First Slice

Business Reporting flow:

**Business Data → Report Specification → Report Asset → Outcome**

Initial capability:

**generate_business_report**

Initial canonical intent goal:

**generate_business_report**

The first workflow should prove that:

- a non-content domain can register a canonical goal;
- the same Intent → Selection → Execution pipeline can execute it;
- the Capability registry/dispatcher can invoke its domain capability;
- Content-specific concepts are not required by the platform core.

## Deferred

- accounting/ERP integrations;
- CRM integrations;
- email delivery;
- dashboards;
- scheduling-specific reporting features;
- marketplace publication;
- autonomous workflow generation;
- cross-domain workflows;
- semantic goal matching.

## Exit Criteria

- business reporting vocabulary exists without importing Content domain models;
- a reporting capability executes through the existing capability architecture;
- a reporting workflow can be selected by its canonical goal;
- the full request-to-execution path works with the second domain;
- no duplicate execution/workflow engine is introduced.
