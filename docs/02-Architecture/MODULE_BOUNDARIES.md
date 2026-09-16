# Module Boundaries

Status: Baseline

The project is a modular monolith. Modules share one deployable runtime but must preserve explicit responsibilities and dependencies.

## Domain

Owns business concepts and business invariants.

Examples:

- Execution
- Workflow
- Capability contracts where they represent business meaning
- domain value objects and policies

The domain must not depend on HTTP, databases, SDKs or external providers.

## Application

Owns use-case orchestration and coordinates domain objects with capabilities and infrastructure-facing ports.

Examples:

- starting an execution;
- advancing execution;
- retry orchestration;
- dispatching a capability.

Application code coordinates; it should not become a second domain model.

## Infrastructure

Owns technical implementations such as persistence, HTTP integrations, provider SDKs and external systems.

Infrastructure details must remain behind explicit boundaries.

## API / Delivery

Owns transport concerns such as HTTP routes, request/response mapping and dependency wiring. API models must not silently become domain models.

## Capability / Plugin Boundary

A capability expresses what the system needs to do. A plugin/provider expresses how that ability is implemented.

Example:

Capability: Transcribe Media

Implementations: Provider A, Provider B, local model, etc.

The core domain should depend on the capability concept, not on a specific provider SDK.

## Dependency Direction

Preferred direction:

Delivery → Application → Domain

Infrastructure implements ports/contracts required by Application or Domain where appropriate.

Domain must remain at the center and independent of infrastructure.

## Boundary Rule

When a feature appears to require a dependency across these boundaries, first ask whether the dependency belongs in the domain, application orchestration, or infrastructure adapter. Do not solve boundary ambiguity by adding direct imports until the design is understood.
