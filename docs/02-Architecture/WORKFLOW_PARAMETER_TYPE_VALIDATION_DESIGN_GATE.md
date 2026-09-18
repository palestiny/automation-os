# Workflow Parameter Type Validation Design Gate

## Status

Accepted — first implementation slice.

## Purpose

Prevent structurally valid intents from selecting workflows when supplied parameter values violate the workflow's declared parameter contract.

## Decisions

1. Required parameter names remain the first contract.
2. A workflow may optionally declare a provider-neutral type for each required parameter.
3. Supported types in this slice are: `string`, `integer`, `number`, `boolean`.
4. Type validation is deterministic and happens before workflow execution.
5. Unknown parameter types are invalid workflow metadata.
6. Missing parameters remain a distinct selection outcome.
7. Type mismatches produce a distinct selection outcome.
8. Extra intent parameters are allowed; the selector does not reject them.
9. No coercion is performed. For example, `"10"` is not accepted as an integer.
10. Python/provider-specific type names do not become part of the workflow contract.
11. Existing workflows with name-only required parameters remain backward compatible.
12. AI does not perform final parameter validation; it only supplies Intent values.
13. No defaults, enums, ranges, formats, nested schemas, or semantic inference are introduced.

## Selection Order

**canonical goal → required parameter presence → declared parameter type validation → selection**

Only a workflow passing all three checks can be selected.

## Deferred

- defaults;
- optional parameter declarations;
- enum/range/format constraints;
- nested objects and arrays;
- coercion;
- semantic parameter inference;
- AI ranking.

## Exit Criteria

- type contracts are provider-neutral;
- invalid values cannot start execution;
- existing workflows remain compatible;
- selection remains deterministic.
