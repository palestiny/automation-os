# Workflow Parameter Requirements Design Gate

## Status

Accepted — design baseline.

## Purpose

Extend deterministic workflow selection beyond exact canonical-goal matching by validating the minimum parameter contract required to execute a workflow.

## Decisions

1. Canonical goal matching remains the first selection criterion.
2. A Workflow may declare provider-neutral required parameter names.
3. Parameter requirements are metadata, not provider-specific schemas.
4. Selection considers only published workflows.
5. A workflow matches only when the Intent goal matches and all required parameter names are present.
6. Missing required parameters produce an explicit no-match outcome for the first slice; no execution starts.
7. Parameter values are not type-coerced by the selector.
8. Parameter value/type validation remains a separate future boundary when concrete domains require it.
9. No AI ranking, fuzzy matching, embeddings, or semantic similarity is introduced.
10. Existing workflows with no declared required parameters remain backward compatible.
11. Workflow definitions remain immutable after publication.
12. The execution engine and Execution lifecycle remain unchanged.

## Rationale

Exact goal matching proves the platform can route intent to a domain workflow. Required-parameter metadata adds a deterministic contract without coupling the shared engine to domain-specific schemas.

## Deferred

- parameter type schemas;
- enum/range/format validation;
- defaults;
- optional parameter semantics;
- semantic parameter inference;
- AI ranking;
- workflow generation;
- autonomous planning.

## TDD Order

1. Add required-parameter vocabulary to Workflow.
2. Add selector tests for complete and incomplete parameter sets.
3. Preserve goal-only workflow compatibility.
4. Add application-level coverage proving incomplete intents never start execution.

## Exit Criteria

- parameter requirements are explicit and provider-neutral;
- incomplete intents cannot select a workflow that requires missing parameters;
- existing workflows remain compatible;
- no execution lifecycle changes are introduced.
