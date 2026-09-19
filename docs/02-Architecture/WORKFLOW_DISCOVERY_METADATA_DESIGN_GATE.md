# Workflow Discovery Metadata Design Gate

## Purpose

Prepare Automation OS to support multiple automation domains and a growing workflow catalog without introducing opaque AI workflow selection.

## Problem

Workflow selection currently matches only Intent.goal against Workflow.supported_goals. This is sufficient for the first slice, but a broader platform needs provider-neutral metadata for discovery, while execution must remain unchanged.

## Committed Decisions

1. Workflow execution semantics remain unchanged.
2. Discovery metadata is descriptive, not executable behavior.
3. Canonical goals remain the primary deterministic compatibility key.
4. A workflow may declare an automation domain/category for discovery.
5. Discovery returns candidates; it does not start execution.
6. Deterministic filtering happens before any future ranking or semantic matching.
7. No AI ranking is introduced in this increment.
8. No workflow generation is introduced.
9. Metadata must not contain provider credentials, SDK objects, or runtime state.
10. Published-state filtering remains mandatory for executable candidates.

## Initial Metadata

The first metadata slice is intentionally small:

- domain: provider-neutral automation domain identifier.
- tags: descriptive discovery tags.
- existing supported_goals: canonical execution compatibility.

All values are immutable once a workflow is published.

## Discovery Boundary

Conceptually:

Intent → Discovery → Candidate Workflows → Selection → Execution

Discovery may narrow the candidate set, but the existing deterministic selection remains authoritative.

## Deferred

- fuzzy/semantic search;
- vector databases;
- AI ranking;
- workflow generation;
- marketplace registration;
- user ratings/reputation;
- dynamic metadata mutation after publication.

## Exit Criteria

- metadata is validated and provider-neutral;
- published workflows expose discovery metadata;
- discovery can filter workflows without executing them;
- existing exact goal selection remains authoritative;
- execution lifecycle is untouched.
