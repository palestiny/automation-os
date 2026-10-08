from __future__ import annotations

import json
from uuid import UUID

from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row

from app.domain.connection import Connection
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.repositories import (
    ConnectionRepository,
    MarketplaceListingRepository,
    ReviewDecisionRepository,
)
from app.domain.review_decision import ReviewDecision
from app.infrastructure.persistence.postgres_mapping import (
    _connection_from_row,
    _marketplace_listing_from_row,
    _review_decision_from_row,
)
from app.infrastructure.persistence.postgres_schema import ConnectionFactory


class PostgresConnectionRepository(ConnectionRepository):
    """PostgreSQL adapter for tenant-owned provider connections."""

    def __init__(self, connection_factory: ConnectionFactory, tenant_id: UUID | None = None) -> None:
        self._connection_factory = connection_factory
        self._tenant_id = tenant_id

    def save(self, connection: Connection) -> None:
        if connection.tenant_id != self._tenant_id:
            raise ValueError("Connection belongs to a different tenant")
        with self._connection_factory() as database:
            try:
                with database.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO connections
                        (id, tenant_id, provider_id, reference, authentication_type,
                         secret_reference, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (connection.id, connection.tenant_id, connection.provider_id,
                     connection.reference, connection.authentication_type,
                     connection.secret_reference, connection.status.value,
                     connection.created_at, connection.updated_at),
                )
                database.commit()
            except UniqueViolation as exc:
                database.rollback()
                raise ValueError("Connection reference or id already exists") from exc

    def get(self, connection_id: UUID) -> Connection | None:
        with self._connection_factory() as database:
            with database.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, tenant_id, provider_id, reference, authentication_type,
                           secret_reference, status, created_at, updated_at
                    FROM connections WHERE id = %s AND tenant_id = %s
                    """,
                    (connection_id, self._tenant_id),
                )
                row = cursor.fetchone()
        return _connection_from_row(row) if row else None

    def get_by_reference(self, reference: str, provider_id: str) -> Connection | None:
        with self._connection_factory() as database:
            with database.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, tenant_id, provider_id, reference, authentication_type,
                           secret_reference, status, created_at, updated_at
                    FROM connections
                    WHERE tenant_id = %s AND reference = %s AND provider_id = %s
                    """,
                    (self._tenant_id, reference.strip(), provider_id.strip()),
                )
                row = cursor.fetchone()
        return _connection_from_row(row) if row else None

    def all(self) -> tuple[Connection, ...]:
        with self._connection_factory() as database:
            with database.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, tenant_id, provider_id, reference, authentication_type,
                           secret_reference, status, created_at, updated_at
                    FROM connections WHERE tenant_id = %s ORDER BY id
                    """,
                    (self._tenant_id,),
                )
                rows = cursor.fetchall()
        return tuple(_connection_from_row(row) for row in rows)


class PostgresMarketplaceListingRepository(MarketplaceListingRepository):
    """PostgreSQL adapter for tenant-owned marketplace listings."""

    def __init__(self, connection_factory: ConnectionFactory, tenant_id: UUID | None = None) -> None:
        self._connection_factory = connection_factory
        self._tenant_id = tenant_id

    def save(self, listing: MarketplaceListing) -> None:
        if listing.tenant_id != self._tenant_id:
            raise ValueError("Marketplace listing belongs to a different tenant")
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO marketplace_listings
                        (id, tenant_id, workflow_id, workflow_version_id, title, description, domain,
                         supported_goals, tags, visibility, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        tenant_id = EXCLUDED.tenant_id,
                        workflow_id = EXCLUDED.workflow_id,
                        workflow_version_id = EXCLUDED.workflow_version_id,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        domain = EXCLUDED.domain,
                        supported_goals = EXCLUDED.supported_goals,
                        tags = EXCLUDED.tags,
                        visibility = EXCLUDED.visibility,
                        status = EXCLUDED.status
                    WHERE marketplace_listings.tenant_id IS NOT DISTINCT FROM EXCLUDED.tenant_id
                    RETURNING id
                    """,
                    (
                        listing.id,
                        self._tenant_id,
                        listing.workflow_id,
                        listing.workflow_version_id,
                        listing.title,
                        listing.description,
                        listing.domain,
                        json.dumps(list(listing.supported_goals)),
                        json.dumps(list(listing.tags)),
                        listing.visibility.value,
                        listing.status.value,
                    ),
                )
                if cursor.fetchone() is None:
                    raise ValueError("Marketplace listing already belongs to a different tenant")
            connection.commit()

    def get(self, listing_id: UUID) -> MarketplaceListing | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, tenant_id, workflow_id, workflow_version_id, title, description, domain,
                           supported_goals, tags, visibility, status
                    FROM marketplace_listings
                    WHERE id = %s AND tenant_id IS NOT DISTINCT FROM %s
                    """,
                    (listing_id, self._tenant_id),
                )
                row = cursor.fetchone()
        return _marketplace_listing_from_row(row) if row else None

    def all(self) -> tuple[MarketplaceListing, ...]:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, tenant_id, workflow_id, workflow_version_id, title, description, domain,
                           supported_goals, tags, visibility, status
                    FROM marketplace_listings
                    WHERE tenant_id IS NOT DISTINCT FROM %s
                    ORDER BY id
                    """,
                        (self._tenant_id,),
                )
                rows = cursor.fetchall()
        return tuple(_marketplace_listing_from_row(row) for row in rows)


# Compatibility alias for existing marketplace persistence consumers.
PostgresMarketplaceRepository = PostgresMarketplaceListingRepository


class PostgresReviewDecisionRepository(ReviewDecisionRepository):
    """PostgreSQL adapter for immutable workflow review decisions."""

    def __init__(self, connection_factory: ConnectionFactory, tenant_id: UUID | None = None) -> None:
        self._connection_factory = connection_factory
        self._tenant_id = tenant_id

    def get_by_idempotency_key(self, key: str) -> ReviewDecision | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, tenant_id, workflow_id, workflow_revision,
                           reviewer_principal_id, decision, reason,
                           idempotency_key, created_at
                    FROM review_decisions
                    WHERE idempotency_key = %s
                      AND tenant_id IS NOT DISTINCT FROM %s
                    """,
                    (key.strip(), self._tenant_id),
                )
                row = cursor.fetchone()
        return _review_decision_from_row(row) if row else None

    def list_by_workflow(self, workflow_id: UUID) -> tuple[ReviewDecision, ...]:
        if not isinstance(workflow_id, UUID):
            raise TypeError("workflow_id must be a UUID")
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, tenant_id, workflow_id, workflow_revision,
                           reviewer_principal_id, decision, reason,
                           idempotency_key, created_at
                    FROM review_decisions
                    WHERE workflow_id = %s
                      AND tenant_id IS NOT DISTINCT FROM %s
                    ORDER BY created_at, id
                    """,
                    (workflow_id, self._tenant_id),
                )
                rows = cursor.fetchall()
        return tuple(_review_decision_from_row(row) for row in rows)

    def save_idempotent(self, decision: ReviewDecision) -> tuple[ReviewDecision, bool]:
        if decision.tenant_id != self._tenant_id:
            raise ValueError("Review decision belongs to a different tenant")
        with self._connection_factory() as connection:
            with connection.transaction():
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO review_decisions
                            (id, tenant_id, workflow_id, workflow_revision,
                             reviewer_principal_id, decision, reason,
                             idempotency_key, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (tenant_id, idempotency_key) DO NOTHING
                        RETURNING id, tenant_id, workflow_id, workflow_revision,
                                  reviewer_principal_id, decision, reason,
                                  idempotency_key, created_at
                        """,
                        (
                            decision.id,
                            decision.tenant_id,
                            decision.workflow_id,
                            decision.workflow_revision,
                            decision.reviewer_principal_id,
                            decision.decision.value,
                            decision.reason,
                            decision.idempotency_key,
                            decision.created_at,
                        ),
                    )
                    row = cursor.fetchone()
                    if row is not None:
                        return _review_decision_from_row(row), True
                    cursor.execute(
                        """
                        SELECT id, tenant_id, workflow_id, workflow_revision,
                               reviewer_principal_id, decision, reason,
                               idempotency_key, created_at
                        FROM review_decisions
                        WHERE idempotency_key = %s
                          AND tenant_id IS NOT DISTINCT FROM %s
                        """,
                        (decision.idempotency_key, self._tenant_id),
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise RuntimeError("Failed to read existing review decision")
                    return _review_decision_from_row(row), False


