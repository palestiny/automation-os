from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.infrastructure.persistence.migrations import PostgresMigrationRunner
from app.infrastructure.persistence.postgres import postgres_connection_factory


def main() -> int:
    database_url = os.environ.get("AUTOMATION_OS_DATABASE_URL")
    if not database_url:
        print("AUTOMATION_OS_DATABASE_URL is required", file=sys.stderr)
        return 2

    applied = PostgresMigrationRunner(
        postgres_connection_factory(database_url)
    ).apply()

    if applied:
        print("Applied migrations:", ", ".join(str(version) for version in applied))
    else:
        print("Database schema is already up to date.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
