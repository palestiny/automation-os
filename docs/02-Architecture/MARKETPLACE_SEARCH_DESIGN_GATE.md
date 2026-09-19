# Marketplace Deterministic Search Design Gate

## Status

Accepted / Implemented.

## Problem

Marketplace discovery currently supports exact filtering by canonical goal and domain. Users also need a deterministic way to find a listing from descriptive text without introducing semantic AI search or a marketplace-specific ranking system.

## Decisions

1. Search is an application-layer discovery concern.
2. Search operates only on listings that already satisfy marketplace publication/discoverability rules.
3. Matching is deterministic and case-insensitive.
4. A search query is tokenized into non-empty whitespace-separated terms.
5. Every query term must match at least one searchable listing field.
6. Searchable fields are title, description, domain, tags, and supported canonical goals.
7. Existing listing order is preserved; no relevance score or ranking is introduced.
8. Search does not create or modify listings or workflows.
9. Search does not introduce semantic embeddings, AI ranking, marketplace-owned goals, or remote plugin discovery.

## TDD Scope

- RED: define query validation and matching behavior.
- GREEN: implement deterministic matching in marketplace discovery.
- REFACTOR: keep search logic inside the application discovery boundary.
- Verify composition with existing publication, visibility, workflow-state, goal, and domain filters.

## Deferred

- semantic search;
- relevance scoring;
- AI ranking;
- marketplace-owned goal registration;
- remote executable plugin search;
- personalization;
- ratings/reviews-based ranking.

## Exit Criteria

- deterministic search behavior is covered by tests;
- unpublished/hidden/unbacked listings remain excluded;
- existing goal/domain filters continue to work;
- no new marketplace execution boundary is introduced.
