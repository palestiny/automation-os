# External Provider Boundary Design Gate

## Purpose

Define how Automation OS keeps third-party providers replaceable without introducing a speculative universal Provider abstraction.

## Problem

The platform already has two provider-facing boundaries:

- `Capability` for execution capabilities.
- `IntentAnalyzer` for request analysis.

Both are provider-neutral. A generic `Provider` interface would not add business meaning and would risk coupling unrelated integrations behind a lowest-common-denominator abstraction.

## Committed Decisions

1. Do not introduce a universal `Provider` domain interface.
2. Provider neutrality is enforced at the boundary that owns the behavior being provided.
3. Capability providers implement `Capability`.
4. Intent-analysis providers implement `IntentAnalyzer`.
5. Provider SDKs, credentials, model names, client construction, and transport details remain infrastructure concerns.
6. Provider-specific configuration is passed through composition/wiring, not stored in domain entities.
7. Multiple providers may implement the same boundary without changing the workflow engine.
8. Provider selection is an application/infrastructure composition concern, not workflow business logic.
9. The platform may add a dedicated provider-selection abstraction only when a real runtime requirement exists (for example fallback, routing, tenant configuration, or cost policy).
10. No provider marketplace, dynamic discovery, remote plugin loading, or automatic model/provider routing is introduced by this gate.

## Consequence

The current architecture already provides the required provider abstraction at the correct behavioral boundaries.

A generic abstraction would currently be speculative and is therefore rejected.

## TDD / Implementation

No production code is required for this gate.

Future provider work must first identify the behavior being provided and implement that behavior's existing boundary.

## Exit Criteria

- Provider SDKs do not leak into domain code.
- Capability and intent-analysis boundaries remain provider-neutral.
- Concrete adapters can be replaced without changing workflow execution.
- No generic abstraction is introduced without a demonstrated requirement.
