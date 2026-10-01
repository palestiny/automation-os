from __future__ import annotations

import os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from app.application.execution_metrics import GetExecutionMetrics
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.connection import Connection, ConnectionRequirement, ConnectionStatus
from app.domain.execution import Execution, ExecutionState
from app.domain.execution_event import ExecutionEvent
from app.domain.marketplace import MarketplaceListing
from app.domain.repositories import ExecutionIdempotencyRepository
from app.domain.review_decision import ReviewDecision, ReviewDecisionType
from app.domain.workflow import Workflow, WorkflowState, WorkflowStep
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.migrations import PostgresMigrationRunner
from app.infrastructure.persistence.postgres import (
    PostgresConnectionRepository,
    PostgresExecutionHistoryRepository,
    PostgresExecutionIdempotencyRepository,
    PostgresExecutionRepository,
    PostgresExecutionStartRepository,
    PostgresMarketplaceListingRepository,
    PostgresMarketplaceRepository,
    PostgresWorkflowRepository,
    PostgresWorkflowVersionRepository,
    PostgresReviewDecisionRepository,
    postgres_connection_factory,
)


DATABASE_URL = os.environ.get("AUTOMATION_OS_TEST_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="AUTOMATION_OS_TEST_DATABASE_URL is required for PostgreSQL persistence tests",
)


@pytest.fixture()
def connection_factory():
    factory = postgres_connection_factory(DATABASE_URL)
    with factory() as connection:
        PostgresMigrationRunner(factory).apply()
        with connection.cursor() as cursor: