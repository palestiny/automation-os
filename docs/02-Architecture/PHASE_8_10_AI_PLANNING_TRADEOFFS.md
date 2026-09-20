# Phase 8.10 — AI Planning Layer Trade-offs

## Decision Status

**Architecture selected: Option A — AI as Plan Proposal.**

## Option A — AI proposes a structured plan — APPROVED

AI is constrained to a provider-neutral proposal contract. Deterministic application services validate the proposal and resolve existing published workflows, versions, and parameters.

**Benefits:** smallest trust boundary; strongest separation from execution; easiest provider replacement; easiest deterministic testing; reuses the immutable WorkflowVersion boundary already established.

**Costs:** less freedom for novel workflow synthesis; richer planning contracts may be needed later.

## Option B — AI generates a complete workflow definition — DEFERRED

AI produces a candidate workflow definition, which deterministic validation would have to accept before a version can be created.

**Benefits:** maximum workflow-generation flexibility; direct path toward future AI-generated workflows.

**Costs:** larger validation surface; tighter coupling between planning and version creation; greater risk of treating model output as executable authority.

## Option C — Deterministic candidate discovery + AI ranking/composition — DEFERRED

The platform first narrows available workflows/capabilities, then AI ranks or composes candidates, followed by deterministic validation.

**Benefits:** limits model search space; reduces references to unknown capabilities; naturally supports future marketplace expansion.

**Costs:** more first-increment orchestration; pulls discovery/ranking semantics into the planner milestone.

## Why Option A was selected

The current platform principle is:

**AI = replaceable planning/tooling**

**Execution + deterministic domain rules = platform authority**

Option A provides the smallest change that introduces AI planning without weakening the boundaries established by workflow versioning, execution lifecycle, persistence, recovery, and metrics.

The first increment therefore accepts a narrower planning capability in exchange for:
- explicit authority boundaries;
- deterministic validation;
- provider replacement;
- testability without a live model;
- no automatic execution;
- no AI-generated version lifecycle.

## Approved scope decisions

1. Existing published WorkflowVersions only.
2. Planner stops at a validated plan.
3. CLARIFICATION_REQUIRED is a first-class outcome.
4. PlannerPort is provider-neutral.
5. AI output is structured data, never arbitrary executable code.

## Reconsideration triggers

A future Design Gate may move from A toward B or C if concrete requirements demonstrate that existing workflow selection/composition cannot satisfy planning needs. Any future expansion must preserve deterministic validation and explicit execution authority.
