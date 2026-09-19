# Phase 8.5 Capability Provider Decision

Status: **APPROVED / IMPLEMENTED IN PR #239**

## Decision

Select **Option A — Application-level Capability Provider Resolver**.

Workflows continue to reference only a stable capability identifier. Provider identity remains outside `WorkflowStep`.

## Resolution Contract

- Multiple providers are supported from the first implementation.
- A capability resolves through one explicitly configured default provider.
- Provider selection is deterministic and configuration-driven.
- No AI, health scoring, marketplace policy, or runtime optimization selects providers in Phase 8.5.
- Missing provider/default provider is an explicit resolution failure.
- Provider identity and capability identity are stable provider metadata.
- Provider construction is explicit through `create()`; lifecycle remains composition-root managed.

## Compatibility

The existing application `CapabilityRegistry` remains as a temporary compatibility input through a resolver adapter so existing concrete capability registrations do not break during migration.

The duplicate legacy `app/core/capabilities/Capability` abstraction is removed. The application-level capability contract is the single capability contract.

## Why

This preserves the architectural separation:

```text
WorkflowStep.capability
        ↓
CapabilityProviderResolver
        ↓
selected CapabilityProvider
        ↓
Capability implementation
```

The workflow definition describes **what** capability is required; provider resolution determines **how** it is implemented.

## Deferred

- remote provider transport;
- provider installation/marketplace;
- provider health and automatic failover;
- AI/policy-based provider selection;
- durable provider configuration;
- authorization and multi-tenancy;
- provider billing.

## Migration Note

The compatibility registry is intentionally not treated as a second provider-selection mechanism. It is an adapter for pre-Phase-8.5 registrations. Future provider implementations should register through `CapabilityProviderResolver`.
