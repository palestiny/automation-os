# Phase 8.5 Design Gate — Capability Provider System

Status: **APPROVED FOR IMPLEMENTATION — Option A selected**

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

## Approved Decision

**Option A — Application-level Capability Provider Resolver** is approved for implementation. The Project Owner's continuation instruction is treated as approval to proceed with the recommended architecture direction.

The implementation will support multiple registered providers from the first version. Selection will remain deterministic and configuration-driven: each capability may have an explicitly designated default provider; no AI, health scoring, marketplace policy, or runtime optimization will select providers in Phase 8.5.

The provider contract will expose stable provider identity and capability identity and will construct the capability implementation through an explicit factory method. Provider lifecycle remains composition-root managed; the provider boundary does not introduce a global service locator or durable configuration.

A capability with no eligible/default provider fails explicitly. Workflow definitions continue to contain only the stable capability identifier; provider identity is not stored in `WorkflowStep`.

## Decision Questions

1. **Multiple providers are supported from the first implementation; one explicit default provider is selected per capability.**
2. **Deterministic rule: resolve the explicitly registered default provider for the requested capability.**
3. **Explicit configuration only in Phase 8.5; policy-based selection is deferred.**
4. **Provider ID and capability ID are required; provider implementation construction is explicit through the provider contract.**
5. **Raise a dedicated provider-resolution error; do not silently fall back to another provider.**
6. **Composition-root managed; providers may construct fresh capability instances through their factory contract.**
7. **Remove the legacy abstraction after migration because the application-level contract is the established capability boundary and no competing contract is justified.**

## Dependency Boundary

Phase 8.5 should establish the provider abstraction needed by later execution, marketplace, and AI-planning capabilities without pulling those later capabilities into this phase.

## Required Exit Criteria

- approved provider architecture;
- RED tests for provider resolution/registration and failure semantics;
- GREEN implementation;
- full regression verification;
- legacy capability abstraction reconciled;
- exit review documenting deferred scope and limitations.