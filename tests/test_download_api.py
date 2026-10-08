import hashlib
import json
from uuid import UUID

from fastapi.testclient import TestClient

from app.application.download_jobs import DownloadJobManager
from app.infrastructure.authentication import EnvironmentApiKeyAuthenticationProvider
from app.infrastructure.persistence.download_jobs import InMemoryDownloadJobRepository
from app.main import app
import app.api.download as download_api
import app.api.job as job_api


def test_download_route_creates_a_job(monkeypatch):
    token = "test-key"
    tenant_id = UUID("00000000-0000-4000-8000-000000000001")
    provider = EnvironmentApiKeyAuthenticationProvider(
        json.dumps([{
            "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
            "principal_id": "test-user",
            "tenant_id": str(tenant_id),
        }])
    )
    monkeypatch.setattr(app.state, "authentication_provider", provider, raising=False)
    manager = DownloadJobManager(InMemoryDownloadJobRepository())
    monkeypatch.setattr(download_api, "job_manager", manager)
    monkeypatch.setattr(job_api, "job_manager", manager)

    class FakeYouTube:
        def download_video(self, url, progress_hook=None):
            return {"title": "test-video", "message": "done"}

    monkeypatch.setattr(download_api, "youtube", FakeYouTube())
    with TestClient(app) as client:
        response = client.post(
            "/download",
            headers={"Authorization": f"Bearer {token}"},
            json={"url": "https://youtu.be/video123"},
        )
        assert response.status_code == 200
        job = client.get(
            f"/jobs/{response.json()['job_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert job.status_code == 200
    assert job.json()["status"] == "completed"



def test_legacy_business_endpoints_require_authentication(monkeypatch):
    token = "configured-test-key"
    monkeypatch.setattr(
        app.state,
        "authentication_provider",
        EnvironmentApiKeyAuthenticationProvider(
            json.dumps([{
                "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
                "principal_id": "test-user",
                "tenant_id": "00000000-0000-4000-8000-000000000001",
            }])
        ),
        raising=False,
    )
    with TestClient(app) as client:
        info = client.post(
            "/info",
            json={"url": "https://youtu.be/video123"},
        )
        job = client.get(f"/jobs/{UUID(int=1)}")
        workflows = client.get("/workflows")

    assert info.status_code == 401
    assert job.status_code == 401
    assert workflows.status_code == 401
