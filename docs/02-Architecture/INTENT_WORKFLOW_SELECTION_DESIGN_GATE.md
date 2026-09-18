# Intent Analysis and Workflow Selection Design Gate

## Status

Proposed — design-only boundary.

## Why Phase 6 Starts Here

Phase 5 established a concrete execution platform: workflows can be defined, triggered, executed, connected to capabilities, and observed.

Phase 6 generalizes the platform from explicit workflow requests toward business intent.

The first boundary must answer:

**What does the user want to accomplish, and which existing workflow can fulfill that intent?**

This is intentionally separated from workflow execution and from AI provider implementation.

## Committed Decisions

1. Intent is business language, not an AI response. Intent represents the requested outcome in provider-neutral terms.
2. Intent analysis is separate from workflow selection. Analysis interprets input into structured intent; selection finds a workflow capable of satisfying it.
3. Workflow execution remains unchanged. Once a workflow is selected, the existing StartWorkflowExecution path remains authoritative.
4. AI is an interchangeable analysis provider. AI may transform natural language into structured intent, but the domain does not depend on a specific model, SDK, or vendor.
5. Workflow selection is deterministic application/domain logic where possible. Matching should be based on explicit workflow metadata/requirements rather than an opaque AI-generated decision.
6. The first slice selects existing published workflows only. Workflow generation is deferred.
7. Ambiguity and no-match are explicit outcomes. They must not silently become arbitrary workflow execution.
8. Intent analysis must not mutate workflows. Generated or modified workflow definitions require a separate policy and lifecycle boundary.
9. Intent is not an Execution. Intent describes requested business outcome; Execution records runtime processing.
10. No autonomous agent loop is introduced by this gate.

## Initial Intent Model

First conceptual shape:

**Intent**
- goal
- parameters

The first implementation should keep the model intentionally small. It must represent business meaning, not provider-specific prompt/response structures.

## Workflow Selection Model

A workflow must expose enough provider-neutral metadata for deterministic selection.

The first selection boundary is:

**Intent → Workflow candidates → Selection result**

Selection outcomes:
- selected workflow;
- no matching workflow;
- ambiguous match.

An ambiguous or missing match is a normal application outcome, not an Execution failure.

## Boundary Responsibilities

### Intent Analyzer

Input: raw user/business request.

Output: structured Intent or an explicit analysis failure/ambiguity.

The analyzer may use an AI provider, rules, or another implementation.

### Workflow Selector

Input: structured Intent and available published workflow definitions.

Output: explicit selection result.

The selector does not execute workflows.

### Workflow Execution

Input: selected workflow id.

Output: existing Execution.

No changes to the execution lifecycle are required.

## AI Boundary

AI-specific concerns remain outside the core domain:
- model SDKs;
- prompts;
- provider credentials;
- token handling;
- provider response formats;
- model-specific retry;
- model routing.

The application may define an IntentAnalyzer protocol so multiple implementations can satisfy the same boundary.

A deterministic fake/rule-based analyzer should be sufficient for the first tests.

## First TDD Increments

### Increment 1 — Intent vocabulary

Define immutable Intent and explicit validation.

### Increment 2 — Intent analysis boundary

Define an analyzer protocol and deterministic test implementation.

### Increment 3 — Workflow selection

Introduce provider-neutral workflow metadata and deterministic matching.

### Increment 4 — Ambiguity/no-match results

Make selection outcomes explicit without starting execution.

### Increment 5 — Intent-to-execution application flow

Connect a uniquely selected workflow to the existing StartWorkflowExecution use case.

### Increment 6 — Concrete AI analyzer

Only after the provider-neutral boundary is stable, add an AI-backed implementation.

## Assumptions

- Existing workflows are sufficient for the first platform-generalization slice.
- Workflow generation is not required to prove intent-driven execution.
- One intent goal with structured parameters is sufficient initially.
- Selection can start with explicit workflow metadata.
- Natural-language analysis can be represented by a replaceable adapter.

## Open Questions

1. What metadata should a Workflow expose for deterministic selection?
2. Should intent goals be strings initially or a typed catalog?
3. How should parameters be validated against workflow requirements?
4. How should confidence be represented when an AI analyzer is used?
5. When does intent require clarification instead of selection?
6. Should workflow generation later produce a draft workflow requiring publication before execution?
7. What policy controls autonomous workflow generation or modification?

## Alternatives Considered

### AI directly selects and executes a workflow

Rejected. It collapses analysis, selection, and execution and makes AI an implicit source of runtime authority.

### AI-owned workflow definitions

Rejected for the first slice. Workflow remains a domain/application object with explicit lifecycle and publication semantics.

### Large intent ontology first

Deferred. A large taxonomy would add complexity before concrete business use cases validate the required vocabulary.

### Workflow generation in the first increment

Deferred. Existing workflow selection proves the platform boundary with less risk.

## Trade-offs

### Deterministic selection vs AI selection

Decision: deterministic selection first.

Trade-off: initial matching is less flexible, but behavior remains explainable, testable, and independent of a model provider.

### Existing workflows vs generated workflows

Decision: existing published workflows first.

Trade-off: fewer autonomous capabilities initially, but workflow lifecycle and governance remain explicit.

### Small Intent model vs rich semantic model

Decision: small model first.

Trade-off: some future concepts will require evolution, but premature ontology design is avoided.

## Deferred Scope

- workflow generation;
- autonomous workflow modification;
- multi-agent planning;
- model routing;
- semantic/vector workflow matching;
- marketplace discovery;
- workflow version optimization;
- long-running planning loops;
- autonomous retries/replanning.

## Design Gate Exit Criteria

- Intent is distinct from Execution.
- Intent analysis is distinct from workflow selection.
- AI is replaceable.
- Selection does not execute.
- Ambiguous/no-match outcomes are explicit.
- Existing StartWorkflowExecution remains authoritative.
- First TDD increment is defined.

## Next Implementation Boundary

**Increment 1 — Intent vocabulary.**
