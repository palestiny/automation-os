# Download Security and Authentication

## Scope

The legacy YouTube download API is retained as a constrained, authenticated feature while its implementation is moved out of the legacy `app/services` and `app/models` locations. Business APIs require a verified tenant identity; only root and health/readiness endpoints are intentionally public.

## Authentication configuration

The API accepts bearer tokens whose SHA-256 digests are configured in `AUTOMATION_OS_API_KEYS_JSON`. The environment variable must contain a JSON array such as:

```json
[
  {
    "token_sha256": "<64-character SHA-256 hex digest>",
    "principal_id": "service-user-1",
    "tenant_id": "00000000-0000-4000-8000-000000000001"
  }
]
```

Generate the digest out of band from a cryptographically random API token and give the original token to the client over a secure channel. Do not commit API tokens or real tenant identifiers. System identities require an explicit `"is_system": true` entry and must not be used for tenant download endpoints. Invalid/missing credentials return 401 when a provider is configured; an unconfigured provider returns 503 rather than pretending authentication is active.

## Download restrictions

- Source URLs must use HTTPS and an explicit supported YouTube hostname.
- URL credentials and arbitrary hostnames are rejected before invoking yt-dlp.
- Playlists are disabled; at most one video is processed per job.
- Downloads are capped at 100 MiB, with a 10-second socket timeout and bounded retries.
- At most two active jobs per tenant are accepted.
- Job records are tenant-scoped and persisted in PostgreSQL when `AUTOMATION_OS_DATABASE_URL` is configured.
- Production mode refuses to initialize the download-job service without PostgreSQL.
- Application URL validation is defense in depth, not a substitute for network egress controls. Production deployments must block loopback, private, link-local, metadata-service, and other internal destinations at the network layer; only required YouTube delivery hosts should be reachable.

## Content and platform terms

Use the API only for content the caller is authorized to access and download. The operator is responsible for complying with applicable law, copyright, and the source platform's terms. The service must not be represented as an official YouTube download API.
