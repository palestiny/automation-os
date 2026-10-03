# AWS Secrets Manager — Production Secret Provider

## Decision

Automation OS uses **AWS Secrets Manager** as the production implementation of the provider-neutral \`SecretProvider\` port.

Runtime boundary:

\`Connection.secret_reference → ResolveRuntimeConnection → SecretProvider → AwsSecretsManagerProvider → AWS Secrets Manager\`

The domain and application layers remain provider-neutral.

## Secret reference contract

Application callers provide a **logical reference**, never an AWS ARN.

The runtime composition establishes a tenant-scoped prefix:

\`<configured-prefix>/<tenant-id>/<logical-reference>\`

Example:

\`automation-os/prod/<tenant-id>/connections/google\`

The provider rejects:
- empty references;
- absolute/ARN references;
- unsupported characters;
- path traversal using \`..\`.

This prevents a caller-controlled connection reference from selecting an arbitrary AWS secret.

## Authentication

Automation OS does not use long-lived AWS access keys in application configuration.

The deployment environment supplies an AWS workload identity supported by the AWS SDK credential chain, such as an ECS task role, EKS workload identity/IRSA, EC2 instance role, or Lambda execution role.

The application does not receive or persist AWS credentials as domain data.

## IAM boundary

The application runtime role receives the minimum permission required to read its allowed secrets:

\`secretsmanager:GetSecretValue\`

If secrets use a customer-managed KMS key, the role also requires the corresponding \`kms:Decrypt\` permission for that key.

The runtime role must not receive secret creation, update, deletion, rotation, or listing permissions merely to execute workflows.

## Rotation

The application always retrieves the current AWS Secrets Manager version through \`GetSecretValue\`.

Secret rotation therefore does not require changing the Automation OS \`Connection\` record as long as its logical reference remains stable.

Rotation mechanisms remain an infrastructure/deployment concern rather than an application-domain concern.

## Failure semantics

Secret resolution:
- validates the logical reference locally;
- uses bounded SDK connect/read timeouts;
- allows bounded SDK retries for transient AWS failures;
- converts provider errors into \`SecretResolutionError\`;
- never includes secret material in the raised application error;
- fails closed when secret material cannot be obtained.

No execution should continue with a missing protected secret.

## Sensitive-data rules

Secret values must never be:
- stored in PostgreSQL;
- placed in \`Connection\`;
- placed in execution history;
- included in capability diagnostics;
- returned by API responses;
- logged by the adapter.

AWS Secrets Manager access is auditable through AWS logging facilities.

## Testing strategy

Unit/contract tests use an injected fake Secrets Manager client. They verify:
- string and binary retrieval;
- reference validation;
- fail-closed behavior;
- sanitized provider errors;
- tenant-prefixed secret identifiers.

A real AWS deployment smoke test is intentionally separate from ordinary CI so CI does not require production AWS credentials.

## Operational note

AWS recommends client-side caching for repeated secret retrievals to improve speed and reduce cost. Caching is intentionally deferred until runtime access frequency is measured; any future cache must preserve tenant isolation and rotation semantics.
