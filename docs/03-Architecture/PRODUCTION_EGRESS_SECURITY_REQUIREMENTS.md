# Production Egress Security Requirements

## Status

**Design contract only. Not an implementation or deployment verification.**

The application-level YouTube source allowlist, HTTPS requirement, credential rejection, default-port restriction, download size cap, and bounded retries are defense in depth. They do not establish complete SSRF protection because the downloader may resolve DNS names, follow redirects, or contact media/CDN hosts as part of extraction.

No deployment platform or production network topology is currently defined in this repository. Therefore this document specifies the required security boundary without choosing AWS, a container platform, a proxy product, or a firewall implementation.

## Threats to control

The download worker must not be able to reach:
- IPv4 or IPv6 loopback addresses;
- private/internal address ranges;
- link-local addresses and cloud metadata endpoints;
- unspecified, multicast, reserved, or otherwise non-public destination ranges;
- internal control-plane, database, cache, or administrative services unless separately and explicitly required;
- arbitrary ports or protocols outside the approved outbound policy.

Controls must apply to the actual connection destination, not only the hostname written in the submitted URL. DNS rebinding, alternate DNS answers, IPv4-mapped IPv6 addresses, redirects, and extractor-initiated secondary requests must be considered.

## Required deployment controls

1. **Enforce outbound policy outside the application.** Use a network firewall/security group, isolated worker network, or an outbound proxy that enforces destination policy at connection time. Application URL parsing alone is insufficient.
2. **Block non-public destinations after DNS resolution.** Reject private, loopback, link-local, metadata, multicast, reserved, and internal destinations for both IPv4 and IPv6. The control must remain effective when DNS answers change between requests.
3. **Cover redirects and secondary requests.** The policy must be enforced for every new connection made by redirects, media manifests, CDN hosts, and the downloader/extractor. Do not assume validating the first URL secures the complete request chain.
4. **Limit outbound protocol and ports.** Permit only the protocols and ports required by the approved download workflow, normally HTTPS over TCP/443. Any additional egress must be justified and recorded.
5. **Isolate the worker.** The download worker should not share unrestricted network reachability with application control-plane services or databases. It should not have cloud instance credentials or metadata access unless there is a documented need.
6. **Keep secrets least-privileged.** Secret retrieval should use the deployment's intended workload identity and narrowly scoped permissions. Do not expose broad cloud credentials to the media extraction process.
7. **Make policy observable.** Record denied egress attempts with bounded, non-secret metadata, and alert on repeated attempts. Avoid logging bearer keys, signed media URLs, or other credentials.

## Verification and evidence

Before production deployment, test from inside the actual worker network:
- direct requests to loopback, private, link-local, and metadata destinations are blocked;
- both IPv4 and IPv6 paths are covered, including IPv4-mapped IPv6;
- a public hostname that resolves to a blocked address is denied at connection time;
- redirects from an allowed public URL to a blocked destination are denied;
- extractor/CDN secondary requests cannot bypass the policy;
- unrelated internal services and database endpoints are unreachable;
- legitimate supported downloads still work under the restricted policy.

Use controlled test endpoints and a non-production environment. Record deployment environment, policy version, test cases, observed outcomes, and date. Mark tests **NOT RUN** if no representative deployment exists; do not infer egress protection from unit tests.

## Acceptance criteria

- [ ] Deployment platform and network enforcement point are selected by the Project Owner / deployment design.
- [ ] Outbound deny rules are implemented and reviewed for IPv4 and IPv6.
- [ ] Redirect, DNS-rebinding, metadata, and internal-service tests pass from the worker network.
- [ ] Legitimate download regression test passes with the policy enabled.
- [ ] Evidence is attached to production-readiness issue #398.
- [ ] Production remains **NO-GO** until the above are verified.

## Related work

- PR #395: download/API authentication and persistence hardening.
- PR #397: source URL authority and port validation.
- Issue #398: production readiness gate.
- `docs/03-Architecture/DOWNLOAD_SECURITY_AND_AUTHENTICATION.md`: application-level download security boundary.
