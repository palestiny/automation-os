"""Compatibility facade for PostgreSQL persistence adapters.

Implementations are split by persistence concern. Existing imports can continue
using this module while new code may import the narrower modules directly.
"""

from app.infrastructure.persistence.postgres_catalog import (
    PostgresConnectionRepository as PostgresConnectionRepository,
    PostgresMarketplaceListingRepository as PostgresMarketplaceListingRepository,
    PostgresMarketplaceRepository as PostgresMarketplaceRepository,
    PostgresReviewDecisionRepository as PostgresReviewDecisionRepository,
)
from app.infrastructure.persistence.postgres_executions import (
    PostgresExecutionHistoryRepository as PostgresExecutionHistoryRepository,
    PostgresExecutionIdempotencyRepository as PostgresExecutionIdempotencyRepository,
    PostgresExecutionRepository as PostgresExecutionRepository,
    PostgresExecutionStartRepository as PostgresExecutionStartRepository,
)
from app.infrastructure.persistence.postgres_schema import (
    ConnectionFactory as ConnectionFactory,
    PostgresSchema as PostgresSchema,
    postgres_connection_factory as postgres_connection_factory,
)
from app.infrastructure.persistence.postgres_workflows import (
    PostgresWorkflowRepository as PostgresWorkflowRepository,
    PostgresWorkflowVersionRepository as PostgresWorkflowVersionRepository,
)

__all__ = [
    "ConnectionFactory",
    "PostgresConnectionRepository",
    "PostgresExecutionHistoryRepository",
    "PostgresExecutionIdempotencyRepository",
    "PostgresExecutionRepository",
    "PostgresExecutionStartRepository",
    "PostgresMarketplaceListingRepository",
    "PostgresMarketplaceRepository",
    "PostgresReviewDecisionRepository",
    "PostgresSchema",
    "PostgresWorkflowRepository",
    "PostgresWorkflowVersionRepository",
    "postgres_connection_factory",
]
