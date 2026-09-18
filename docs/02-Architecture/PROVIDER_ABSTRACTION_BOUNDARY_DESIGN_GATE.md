# Provider Abstraction Boundary Design Gate

## Status

Proposed.

## Problem

Automation OS now has multiple provider-facing boundaries:

- Capability implementations such as media acquisition and publishing.
- AI intent analysis implementations.

It is tempting to introduce one universal `Provider` interface or registry. That would make technically similar concerns look identical even though their business contracts, lifecycle, failure semantics, and configuration needs differ.

## Decisions

1. There will be no universal `Provider` protocol in the current modular monolith.
2. Provider abstraction remains contract-specific:
   - capabilities use `Capability` and `CapabilityRegistry`;
   - intent analysis uses `IntentAnalyzer`;
   - persistence uses repository contracts;
   - scheduling uses scheduling/application boundaries.
3. Provider SDKs remain infrastructure concerns.
4. Provider selection is an application/infrastructure composition concern, not a domain concern.
5. A concrete provider must implement an existing business/technical boundary rather than introduce a parallel provider-facing domain model.
6. Provider-specific configuration, credentials, client construction, and lifecycle remain outside domain objects.
7. A shared abstraction may be introduced later only when at least two independent contracts demonstrate identical behavior and the abstraction removes real duplication.
8. Marketplace/provider discovery is not implied by this decision.

## Why

A universal provider abstraction would currently provide naming consistency but little behavioral value. It risks leaking infrastructure concepts into unrelated contracts and creating a second abstraction layer over Capability, IntentAnalyzer, and repositories.

The existing boundaries already provide replaceability where replacement has business value.

## TDD / Implementation Consequence

No production code is required for this gate.

Future provider work must first implement the relevant existing contract. If repeated provider concerns emerge, a new Design Gate must demonstrate the duplication and define the smallest shared abstraction.

## Deferred

- universal Provider protocol;
- universal ProviderRegistry;
- provider marketplace;
- automatic provider selection;
- health-based provider routing;
- provider fallback orchestration;
- model/provider routing policies.

## Exit Criteria

- provider-facing contracts remain explicit and independent;
- no SDK leaks into domain;
- provider replacement remains possible at each boundary;
- future abstraction requires evidence rather than anticipation.
