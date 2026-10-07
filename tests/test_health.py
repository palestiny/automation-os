from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_liveness_does_not_require_database(monkeypatch):
    monkeypatch.delenv("AUTOMATION_OS_DATABASE_URL", raising=False)

    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"process": "ok"},
    }


def test_readiness_fails_closed_when_database_is_not_configured(monkeypatch):
    monkeypatch.delenv("AUTOMATION_OS_DATABASE_URL", raising=False)

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "not_configured"},
    }


def test_readiness_uses_database_probe(monkeypatch):
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def execute(self, query):
            assert query == "SELECT version FROM schema_migrations ORDER BY version"

        def fetchall(self):
            from app.infrastructure.persistence.migrations import MIGRATIONS
            return [(migration.version,) for migration in MIGRATIONS]

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def cursor(self):
            return FakeCursor()

    monkeypatch.setenv("AUTOMATION_OS_DATABASE_URL", "postgresql://example")
    monkeypatch.setattr(
        "app.application.health.psycopg.connect",
        lambda *_args, **_kwargs: FakeConnection(),
    )

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok"},
    }

def test_readiness_rejects_incomplete_migrations(monkeypatch):
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def execute(self, query):
            assert query == "SELECT version FROM schema_migrations ORDER BY version"

        def fetchall(self):
            return []

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def cursor(self):
            return FakeCursor()

    monkeypatch.setenv("AUTOMATION_OS_DATABASE_URL", "postgresql://example")
    monkeypatch.setattr(
        "app.application.health.psycopg.connect",
        lambda *_args, **_kwargs: FakeConnection(),
    )

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "migrations_incomplete"},
    }
