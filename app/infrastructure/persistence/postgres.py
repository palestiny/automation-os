"""Compatibility facade for PostgreSQL persistence adapters.

Implementations are split by persistence concern. Existing imports can continue
using this module while new code may import the narrower modules directly.
"""

from app.infrastructure.persistence.postgres_catalog import (
    PostgresConnectionRepository as PostgresConnectionRepository,
)
from app.infrastructure.persistence.postgres_catalog import (
    PostgresMarketplaceListingRepository as PostgresMarketplaceListingRepository,
)
from app.infrastructure.persistence.postgres_catalog import (
    PostgresMarketplaceRepository as PostgresMarketplaceRepository,
)
from app.infrastructure.persistence.postgres_catalog import (
    PostgresReviewDecisionRepository as PostgresReviewDecisionRepository,
)
from app.infrastructure.persistence.postgres_executions import (
    PostgresExecutionHistoryRepository as PostgresExecutionHistoryRepository,
)
from app.infrastructure.persistence.postgres_executions import (
    PostgresExecutionIdempotencyRepository as PostgresExecutionIdempotencyRepository,
)
from app.infrastructure.persistence.postgres_executions import (
    PostgresExecutionRepository as PostgresExecutionRepository,
)
from app.infrastructure.persistence.postgres_executions import (
    PostgresExecutionStartRepository as PostgresExecutionStartRepository,
)
from app.infrastructure.persistence.postgres_schema import (
    ConnectionFactory as ConnectionFactory,
)
from app.infrastructure.persistence.postgres_schema import (
    PostgresSchema as PostgresSchema,
)
from app.infrastructure.persistence.postgres_schema import (
    postgres_connection_factory as postgres_connection_factory,
)
from app.infrastructure.persistence.postgres_workflows import (
    PostgresWorkflowRepository as PostgresWorkflowRepository,
)
from app.infrastructure.persistence.postgres_workflows import (
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
