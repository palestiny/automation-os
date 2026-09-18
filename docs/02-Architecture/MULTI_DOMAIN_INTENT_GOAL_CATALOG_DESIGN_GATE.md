# Multi-Domain Intent Goal Catalog Design Gate

## Status

Accepted

## Purpose

Allow additional automation domains to contribute canonical intent goals without changing the workflow execution engine.

## Decisions

1. Canonical goals remain provider-neutral strings.
2. A goal catalog can be composed from multiple domain-owned catalogs.
3. Composition rejects duplicate canonical goals rather than silently overriding them.
4. The execution engine remains unaware of automation-domain ownership.
5. Domain ownership is represented by how catalogs are composed, not by adding domain state to Workflow or Execution.
6. Existing goal identifiers remain valid; namespacing is not introduced in this increment.
7. Goal validation remains mandatory before deterministic workflow selection.
8. AI adapters may consume the resulting aggregate catalog, but do not own it.
9. No dynamic runtime discovery or marketplace registration is introduced.

## Example

Content domain catalog:

`create_short_video`, `publish_content`

Business domain catalog:

`generate_report`, `send_report`

Platform composition:

**domain catalogs → aggregate IntentGoalCatalog → Intent validation → workflow selection**

## Deferred

- plugin-owned dynamic goal registration;
- marketplace discovery;
- semantic goal matching;
- automatic goal generation;
- domain-specific AI models;
- runtime catalog mutation.

## Exit Criteria

- two independent domain catalogs can be combined;
- duplicate goals fail explicitly;
- existing selection/execution behavior is unchanged;
- no domain-specific dependency enters the execution engine.
