# Intent Goal Catalog Design Gate

## Status

Accepted

## Purpose

Make AI intent analysis safe for deterministic workflow selection as the platform grows beyond one automation domain.

## Problem

`Workflow.supported_goals` currently uses exact string identifiers. An AI analyzer can produce a structurally valid but unsupported goal. Structural validity alone does not guarantee that the goal is executable.

## Decisions

1. Workflow selection remains deterministic and exact.
2. A goal is executable only when it belongs to the platform's known goal catalog.
3. AI analysis may classify a request only into known canonical goals.
4. The AI adapter must not invent workflow identifiers or select workflows.
5. Unknown goals remain an explicit analysis/validation outcome and must not reach execution.
6. The catalog is provider-neutral and lives outside the AI SDK adapter.
7. Multiple automation domains can contribute canonical goals without changing the execution engine.
8. Workflow metadata continues to declare which canonical goals it supports.
9. No semantic/vector matching is introduced in this increment.
10. No automatic workflow generation is introduced.

## Shape

Conceptually:

**Domain → Goal ID → Workflow**

Examples:

- content → create_short_video
- content → publish_content
- business → generate_report

The exact initial catalog is intentionally small.

## Boundary Validation

The intent-to-execution application boundary also validates the catalog so non-AI callers cannot bypass canonical goal validation.

## Safety Rule

The system must never execute a workflow solely because an AI provider returned a plausible string.

The path must remain:

**request → analyzed canonical goal → deterministic selection → existing execution use case**

## Deferred

- embeddings/vector search;
- fuzzy goal matching;
- AI-generated goals;
- workflow generation;
- autonomous planning;
- marketplace-owned goal registration.

## Implementation Status

Implemented in PR #126 and hardened at the intent-to-execution boundary in PR #130. The catalog is now enforced when configured, and an unregistered goal cannot start execution.

## Status

Accepted and implemented.

## Exit Criteria

Implementation status: accepted and implemented in application boundaries. The canonical catalog is enforced by the OpenAI adapter when configured and by intent-to-execution when a catalog is supplied.


- canonical goal validation is provider-independent;
- unknown goals cannot start executions;
- multiple domains can register goals without modifying the execution engine;
- existing workflow selection behavior remains deterministic.
