# Workflow Discovery API Metadata Design Gate

## Status

Accepted — implementation may proceed.

## Problem

The workflow discovery application boundary already supports provider-neutral metadata filters (automation_domain and tags) and published-state filtering. The HTTP workflow listing currently exposes only the canonical-goal filter and does not expose the discovery metadata returned by the workflow model.

This leaves the public discovery boundary behind the committed discovery metadata design.

## Committed Decisions

1. Keep the existing `GET /workflows` endpoint as the read-only discovery API.
2. Expose `automation_domain` as an optional query parameter.
3. Expose `tag` as a repeatable query parameter so callers can require all supplied tags.
4. Continue exposing `goal` as the canonical compatibility filter.
5. Expose workflow discovery metadata in `WorkflowResponse`.
6. Keep published-state filtering mandatory.
7. Discovery remains deterministic and read-only.
8. Discovery never starts execution.
9. No ranking, fuzzy/semantic matching, pagination, authentication, marketplace registration, or workflow generation is introduced.
10. Existing callers that use only `goal` retain the same behavior.

## Query Semantics

- `goal`: exact canonical supported-goal match.
- `automation_domain`: exact provider-neutral domain match.
- `tag`: repeatable exact tag match; all supplied tags must be present.
- omitted filters: return all published workflows.

## Response Metadata

Each workflow response exposes:

- `automation_domain`
- `discovery_tags`

The metadata is descriptive and does not change execution semantics.

## TDD Order

1. RED: API exposes discovery metadata.
2. RED: domain filter narrows results.
3. RED: repeated tag filters require all tags.
4. GREEN: extend application query and response mapping.
5. REFACTOR: preserve the existing deterministic discovery boundary.

## Exit Criteria

- HTTP discovery supports goal, domain, and tag filtering.
- Published workflows expose discovery metadata.
- Existing goal-only behavior remains green.
- No execution path is touched.