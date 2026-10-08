from fastapi import FastAPI

from app.api.download import router as download_router
from app.api.execution import router as execution_router
from app.api.health import router as health_router
from app.api.info import router as info_router
from app.api.job import router as job_router
from app.api.review import router as review_router
from app.api.workflow import router as workflow_router
from app.infrastructure.authentication import (
    AuthenticationMiddleware,
    EnvironmentApiKeyAuthenticationProvider,
)
from app.infrastructure.observability import (
    RequestObservabilityMiddleware,
    configure_observability_logging,
)

configure_observability_logging()

app = FastAPI(
    title="Automation OS",
    version="1.0.0",
)
app.state.authentication_provider = EnvironmentApiKeyAuthenticationProvider()

app.add_middleware(RequestObservabilityMiddleware)
app.add_middleware(AuthenticationMiddleware)

app.include_router(download_router)
app.include_router(info_router)
app.include_router(job_router)
app.include_router(execution_router)
app.include_router(workflow_router)
app.include_router(review_router)
app.include_router(health_router)


@app.get("/")
def root():
    return {"message": "Automation OS"}
