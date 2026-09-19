# External Provider Abstraction Design Gate

## Status

Accepted and implemented.

## Purpose

Define the smallest provider abstraction that can support multiple infrastructure providers without creating a second domain model or forcing unrelated capabilities into one generic interface.

## Problem

Automation OS already isolates providers at capability and intent-analysis boundaries. As more automation domains and providers are added, provider configuration and lifecycle concerns must remain outside domain objects while preserving replaceability.

## Committed Decisions

1. Provider abstraction is an infrastructure/application concern, not a domain entity.
2. Existing business boundaries remain authoritative:
   - `Capability` for executable automation behavior.
   - `IntentAnalyzer` for request interpretation.
3. No universal `Provider.execute()` interface will replace those boundaries.
4. Provider identity/configuration may be represented by small infrastructure value objects where needed.
5. Provider-specific credentials, SDK clients, endpoints, models, and configuration remain infrastructure-owned.
6. Business workflows reference capabilities, never provider implementations.
7. Provider selection is explicit configuration for the first slice; automatic provider routing is deferred.
8. A provider adapter may implement more than one application port only when the contracts are independently satisfied; adapters must not leak provider-specific types across boundaries.
9. Tests use fake provider implementations at each application port.
10. No provider registry, marketplace provider installation, health-routing, failover, or dynamic discovery is introduced by this gate.

## Boundary

The intended dependency direction is:

**Application Port → Infrastructure Adapter → External Provider**

Never:

**Domain → Provider**

and never:

**Workflow → Provider**

## Configuration

Provider configuration belongs at composition/bootstrap boundaries.

Examples include:

- provider name/id;
- model or service identifier;
- credentials reference;
- endpoint configuration.

Secrets themselves are not part of domain or workflow definitions.

## Why Not One Generic Provider Port?

Capabilities and analyzers have different contracts, failure semantics, and business meanings. A universal provider interface would erase useful boundaries and create conditional behavior in callers.

## First Implementation Slice

1. Document provider configuration boundary.
2. Introduce only the minimal provider identity/configuration object if an existing concrete adapter needs it.
3. Refactor one existing adapter as proof of the boundary.
4. Verify no domain/application business object imports provider SDK types.
5. Keep all existing runtime behavior unchanged.

## Deferred

- provider registry;
- automatic provider selection;
- fallback/failover;
- health checks;
- model routing;
- provider marketplace;
- remote providers;
- dynamic plugin discovery;
- secret manager integration;
- distributed provider workers.

## Exit Criteria

- Provider abstraction is additive rather than replacing existing application ports.
- Provider-specific concerns remain infrastructure-owned.
- Existing capability and intent boundaries remain independently testable.
- At least one adapter demonstrates the boundary without changing business behavior.

## Implementation Result

`ProviderConfiguration` now owns provider/service identity, optional endpoint, and credentials reference at the infrastructure boundary. The OpenAI intent analyzer consumes this configuration while retaining the existing `IntentAnalyzer` application contract.
