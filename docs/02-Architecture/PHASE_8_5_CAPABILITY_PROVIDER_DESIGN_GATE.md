# Phase 8.5 Design Gate — Capability Provider System

Status: **DESIGN PREPARATION — decision pending**

Capability: **Capability Provider System**
Position: **5 of 13**

## Objective

Introduce a provider-independent capability boundary so a workflow references a stable capability contract while concrete implementations/providers can be selected or replaced without changing the workflow definition.

## Repository Evidence

The repository already contains an application-level `Capability` protocol, `CapabilityRegistry`, `CapabilityFactory`, `CapabilityDispatcher`, and `CapabilityResult`. `WorkflowStep` currently stores a capability identifier and `ExecuteWorkflowStep` delegates execution through `CapabilityDispatcher`.

Repository inspection also found an older parallel `app/core/capabilities/Capability` abstraction. This is architectural duplication and must be reconciled before the provider system is considered complete; a second competing capability contract should not be introduced.

## In Scope

- provider-independent capability identity;
- explicit provider implementation contract;
- deterministic provider resolution/selection boundary;
- capability-to-provider registration;
- clear behavior when no provider is available;
- focused tests and full regression;
- reconciliation of the duplicate legacy capability abstraction.

## Out of Scope

- external marketplace/provider installation;
- remote provider transport;
- automatic provider health monitoring;
- billing;
- multi-tenancy/authorization;
- AI-based provider selection;
- durable provider configuration;
- workflow versioning;
- generic service discovery infrastructure.

## Current Architectural Pressure

The existing application layer separates capability identity from execution through `CapabilityDispatcher`, but the current registry resolves a concrete capability instance directly by capability ID. The factory also constructs concrete capabilities directly by capability ID. Provider replacement is therefore currently a composition-time concern and provider identity/selection is not modeled explicitly.

## Candidate Options

### Option A — Application-level Capability Provider Resolver

Keep `WorkflowStep.capability` as a stable capability ID. Introduce an application-level provider contract and resolver that maps a capability ID to an eligible provider implementation, then let `CapabilityDispatcher` invoke the resolved implementation.

Pros: preserves workflow/provider separation; keeps provider selection outside the domain; supports multiple providers; deterministic and testable; aligns with the existing application dispatcher.

Trade-offs: introduces one more application boundary; provider selection policy must be explicitly defined.

### Option B — Provider-aware Capability Registry

Extend the existing registry so a capability ID may have multiple provider implementations and the registry itself resolves the provider.

Pros: fewer application services; centralizes registration and resolution.

Trade-offs: registry becomes responsible for provider-selection policy; lifecycle and configuration concerns can accumulate inside the registry; harder to keep lookup separate from selection policy.

### Option C — Provider Identity in Workflow Steps

Allow workflow steps to reference both a capability ID and provider ID.

Pros: explicit provider pinning; deterministic execution target.

Trade-offs: couples workflow definitions to implementation/provider identity; weakens provider interchangeability; increases versioning and marketplace coupling.

## Recommended Decision Direction

**Option A is the recommended architecture direction**, subject to Project Owner approval. It preserves the established rule that workflows describe what should happen while provider selection determines how the capability is implemented.

This recommendation does not authorize GREEN implementation until the Project Owner approves the architectural choice.

## Decision Questions

1. Should a capability have one default provider or support multiple providers from the first implementation?
2. If multiple providers exist, what deterministic selection rule applies?
3. Should provider selection be explicit configuration only, or may policy choose among registered providers?
4. What provider identity and metadata belong in the provider contract?
5. What is the failure contract when a capability exists but no eligible provider exists?
6. Are provider instances singleton, transient, or composition-root managed?
7. Should the legacy `app/core/capabilities/Capability` abstraction be removed after migration, or retained only if a concrete use remains?

## Dependency Boundary

Phase 8.5 should establish the provider abstraction needed by later execution, marketplace, and AI-planning capabilities without pulling those later capabilities into this phase.

## Required Exit Criteria

- approved provider architecture;
- RED tests for provider resolution/registration and failure semantics;
- GREEN implementation;
- full regression verification;
- legacy capability abstraction reconciled;
- exit review documenting deferred scope and limitations.