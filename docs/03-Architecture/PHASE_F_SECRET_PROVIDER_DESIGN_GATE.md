# Phase F — Production Secret Provider Design Gate

## Status

**DESIGN DECISION REQUIRED**

The application already has a provider-neutral `SecretProvider` port and a fail-closed `UnconfiguredSecretProvider`. Phase F selects the production secret-management architecture and defines the adapter boundary before implementation.

## Existing Boundary

`Connection.secret_reference` is persisted, not the secret material.

Runtime resolution is:

`ConnectionResolver → ResolveRuntimeConnection → SecretProvider → ResolvedConnection`

The application/domain layers must not depend on a specific secret-management vendor.

## Required Properties

The production provider must:

1. resolve secrets by opaque reference;
2. never persist secret material in the Automation OS database;
3. fail closed when a reference is missing or inaccessible;
4. provide least-privilege access from the application runtime;
5. support secret rotation without changing domain `Connection` records;
6. avoid placing secret values in logs, exceptions, execution history, or API responses;
7. provide an auditable access boundary;
8. support local/test substitution without weakening production behavior;
9. define timeout/error semantics;
10. support the deployment environment selected for Automation OS.

## Options

### Option A — HashiCorp Vault

**Architecture:** Automation OS uses a Vault adapter implementing `SecretProvider`.

**Advantages**
- strong provider-neutral/self-hosted model;
- explicit secret paths and policies;
- good fit when the product may deploy across clouds;
- mature authentication and audit concepts.

**Trade-offs**
- introduces Vault as another production infrastructure component;
- availability and operational ownership become part of the platform;
- application authentication to Vault must itself be designed securely.

### Option B — Cloud-native secret manager

Examples include AWS Secrets Manager, Azure Key Vault, or Google Secret Manager.

**Advantages**
- integrates naturally with the selected cloud identity model;
- avoids operating a separate Vault cluster;
- managed availability and rotation features.

**Trade-offs**
- creates stronger cloud coupling;
- exact adapter/authentication behavior depends on the selected cloud;
- multi-cloud portability requires additional adapters.

### Option C — Kubernetes Secret / platform-native secret store

Use the deployment platform's secret injection mechanism and expose a small runtime adapter.

**Advantages**
- simple for Kubernetes-first deployments;
- minimal application dependency surface.

**Trade-offs**
- security and rotation guarantees depend heavily on the cluster/platform configuration;
- raw Kubernetes Secret storage is not equivalent to a dedicated external secret-management system;
- portability outside Kubernetes is weaker.

### Option D — Environment-variable secrets

Inject secrets directly into the process environment.

**Advantages**
- simplest deployment mechanism;
- no external secret API dependency.

**Trade-offs**
- weaker lifecycle/rotation ergonomics;
- greater risk of accidental exposure through process/debug tooling;
- poor fit for a serious multi-tenant automation platform;
- weak auditability at the application secret-reference boundary.

**Phase F production recommendation:** do not use environment variables as the durable production secret-management architecture.

## Decision Rule

The final provider should be selected primarily from the actual deployment target:

- **AWS-first:** AWS Secrets Manager is the natural cloud-native option.
- **Azure-first:** Azure Key Vault is the natural cloud-native option.
- **GCP-first:** Google Secret Manager is the natural cloud-native option.
- **Multi-cloud / self-hosted portability is a first-class requirement:** HashiCorp Vault is the strongest candidate.
- **Kubernetes-only with an existing enterprise secret platform:** integrate with that platform rather than introducing a second store.

## Security Contract Regardless of Provider

The adapter must expose only:

`get_secret(secret_reference) → protected secret material`

The adapter must not expose provider-specific objects to the domain.

Secret material must be treated as sensitive in memory and must never be:
- serialized into `Connection`;
- persisted into execution history;
- included in capability diagnostics;
- returned through API responses;
- written to normal application logs.

## Acceptance Criteria

Before Phase F can be marked PASS:

1. one concrete provider is selected;
2. authentication from Automation OS to that provider is defined;
3. least-privilege policy is documented;
4. secret-reference naming/namespace rules are defined;
5. rotation behavior is defined;
6. timeout/error behavior is defined;
7. fail-closed behavior is tested;
8. secret material is proven absent from persisted execution evidence;
9. integration tests use a safe test secret;
10. the provider adapter remains replaceable behind `SecretProvider`.

## Non-goals

Phase F does not redesign the `Connection` aggregate, runtime connection preparation, execution orchestration, or multi-tenant authorization model.

## Gate Decision

**BLOCKED pending Project Owner selection of the production deployment target/provider.**
