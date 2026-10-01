# PostgreSQL Migration Boundary

## Decision

PostgreSQL schema lifecycle is an explicit migration concern.

Runtime dependency composition must not create or mutate database schema.

## Migration ownership

- Migration definitions: `app/infrastructure/persistence/migrations.py`
- Migration tracking table: `schema_migrations`
- Runner: `PostgresMigrationRunner`
- Runtime repositories: `app/infrastructure/persistence/postgres.py`

The migration runner applies each version once and records the version transactionally with its schema changes.

## Operational rule

A deployment must apply database migrations before starting application instances that require PostgreSQL.

Application startup/runtime dependency composition must only create repository adapters against an already-prepared schema.

## Current migration

Version 1 creates the existing Automation OS PostgreSQL schema and preserves the current table/index contract.

Future schema changes must be new forward migrations. Do not edit an already-applied migration to change production schema history.

## Local/CI verification

Set `AUTOMATION_OS_TEST_DATABASE_URL` to a PostgreSQL database and run the migration test suite.

The persistence tests use the explicit migration runner before exercising repositories.

## Non-goals

This boundary does not introduce:
- a third-party migration framework;
- automatic migrations at application startup;
- destructive down migrations;
- a new database technology.
