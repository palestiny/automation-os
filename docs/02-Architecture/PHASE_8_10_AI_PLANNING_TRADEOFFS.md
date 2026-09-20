# Phase 8.10 — AI Planning Layer Trade-offs

## Decision Status

No architecture is selected yet. The Design Gate is Draft.

## Option A — AI proposes a structured plan

AI is constrained to a provider-neutral proposal contract. Deterministic application services validate the proposal and resolve registered workflows, versions, and parameters.

**Benefits:** smallest trust boundary; strongest separation from execution; easiest provider replacement; easiest deterministic testing.

**Costs:** less freedom for novel workflow synthesis; richer planning contracts may be needed later.

## Option B — AI generates a complete workflow definition

AI produces a candidate workflow definition, which deterministic validation must accept before a version can be created.

**Benefits:** maximum workflow-generation flexibility; direct path toward future AI-generated workflows.

**Costs:** larger validation surface; tighter coupling between planning and version creation; greater risk of treating model output as executable authority.

## Option C — Deterministic candidate discovery + AI ranking/composition

The platform first narrows available workflows/capabilities, then AI ranks or composes candidates, followed by deterministic validation.

**Benefits:** limits model search space; reduces references to unknown capabilities; naturally supports future marketplace expansion.

**Costs:** more first-increment orchestration; pulls discovery/ranking semantics into the planner milestone.

## Decision pressure

The key architectural question is not whether AI is useful. It is where AI authority stops.

The current platform principle is:

AI = replaceable planning/tooling

Execution + deterministic domain rules = platform authority

Any selected architecture must preserve that boundary.

## Reconsideration triggers

A future Design Gate may move from A toward B or C if concrete requirements demonstrate that existing workflow selection/composition cannot satisfy planning needs. Such a move must preserve deterministic validation and explicit execution authority.
