# Phase G — Observability + CI Hardening Design Gate

## Status

**FIRST OPERATIONAL/CI SLICE PASS — independently verified on master**

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

## Verification evidence

GitHub Actions run [#2099](https://github.com/palestiny/automation-os/actions/runs/37849394172) executed on `master` at commit `27e897cb65bdde73ce0277ef44cac75d6add4bfa` and concluded **success**.

Verified job steps include:
- dependency installation and `pip check`;
- Ruff syntax-error gate;
- Python compile check;
- PostgreSQL migration application;
- full pytest suite with coverage;
- dependency audit via `pip-audit`.

This closes the first operational/CI slice only. It is not a production deployment certification.

## Non-goals

- no domain changes;
- no execution-state changes;
- no distributed tracing implementation yet;
- no metrics backend/vendor;
- no SLO/alerting configuration;
- no logging of sensitive request data.

## Acceptance criteria result

1. Correlation ID implementation is included in the merged first slice.
2. Request completion logging is included with bounded operational metadata.
3. Invalid/oversized request IDs are handled by the implementation.
4. Sensitive request headers are excluded from request middleware logs.
5. Existing API behavior is intended to remain unchanged apart from the response correlation header.
6. CI runs compile check, dependency check, migrations, and full tests.
7. The post-merge `master` workflow succeeded.

## Exit decision

**PASS — close Phase G's first operational/CI slice.**

Further observability work (provider metrics, tracing, SLOs, dashboards, alerting, broader quality gates) remains explicitly tracked and must be justified by operational requirements rather than silently included in this phase.
