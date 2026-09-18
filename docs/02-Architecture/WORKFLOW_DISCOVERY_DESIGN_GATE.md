# Workflow Discovery Design Gate

## Status

Proposed.

## Purpose

Define how the platform exposes executable workflows as discoverable business capabilities without introducing AI-driven workflow selection.

## Decisions

1. Workflow discovery is a read/query concern.
2. Discovery returns published workflows only.
3. Discovery is based on explicit provider-neutral metadata.
4. Discovery may filter by canonical intent goal.
5. Discovery does not execute workflows.
6. Discovery does not infer or rank workflows using AI.
7. Discovery does not mutate workflow definitions.
8. Existing deterministic `SelectWorkflow` remains authoritative for execution selection.
9. Discovery may later support multiple domains through metadata, without changing the execution engine.
10. No marketplace behavior is introduced in this slice.

## Minimum Query

A discovery query may contain a canonical goal.

The result contains the matching published workflow definitions or their identifiers, depending on the application use case.

## Relationship to Selection

Discovery answers:

**"What published workflows are available for this goal?"**

Selection answers:

**"Can exactly one workflow be selected for this Intent?"**

These remain separate concerns.

## Deferred

- semantic/vector discovery;
- AI ranking;
- relevance scoring;
- marketplace search;
- provider capability health;
- dynamic workflow generation;
- autonomous workflow optimization.

## Exit Criteria

- published-only discovery is explicit;
- canonical-goal filtering is deterministic;
- discovery cannot start execution;
- existing selection semantics remain unchanged.
