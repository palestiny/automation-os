# Phase G — Observability + CI Hardening Design Gate

## Status

**IMPLEMENTATION COMPLETE — post-merge master verification pending**

## Objective

Make operational behavior diagnosable without changing domain or execution semantics, and raise CI from tests-only to a small set of deterministic engineering-quality gates.

## Observability decision

Use standard-library logging plus a small application-owned observability boundary.

Each HTTP request receives a correlation ID:
- accept X-Request-ID only as a correlation hint;
- validate and bound it;
- generate a UUID when absent/invalid;
- return the correlation ID in the response;
- include it in structured request logs.

Request logs contain only operational metadata:
- event name;
- correlation ID;
- HTTP method;
- route/path;
- status code;
- duration milliseconds.

No query strings, authorization headers, cookies, request bodies, or exception payloads are logged by this middleware.

The implementation intentionally avoids introducing a logging framework or OpenTelemetry dependency before operational requirements justify it.

## CI decision

Keep PostgreSQL integration as the authoritative test gate and add deterministic checks that do not depend on production infrastructure:

1. dependency consistency via pip check;
2. Python bytecode compilation via python -m compileall -q app tests;
3. full pytest suite.

The repository now has a non-breaking Ruff syntax gate (`ruff check app tests scripts --select E9`). Broader lint/type/security enforcement remains deferred until compatibility and scope are explicitly measured.

## Non-goals

- no domain changes;
- no execution-state changes;
- no distributed tracing implementation yet;
- no metrics backend/vendor;
- no SLO/alerting configuration;
- no logging of sensitive request data.

## Acceptance criteria

1. Every HTTP response has a bounded correlation ID.
2. Request completion logs contain correlation ID, path, status, and duration.
3. Invalid/oversized request IDs are replaced, not trusted.
4. Sensitive request headers are not logged.
5. Existing API behavior remains unchanged apart from the response correlation header.
6. CI runs compile check, dependency check, migrations, and full tests.
7. Existing test suite remains green.

## Exit condition

After the merged changes are independently verified on `master`, close Phase G's first operational slice. Further observability work (provider metrics, tracing, SLOs) remains explicitly tracked rather than hidden inside this change.
