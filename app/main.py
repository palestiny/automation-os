from fastapi import FastAPI

from app.api.download import router as download_router
from app.api.info import router as info_router
from app.api.job import router as job_router
from app.api.execution import router as execution_router
from app.api.workflow import router as workflow_router

app = FastAPI(
    title="Automation OS",
    version="1.0.0",
)

app.include_router(download_router)
app.include_router(info_router)
app.include_router(job_router)
app.include_router(execution_router)
app.include_router(workflow_router)


@app.get("/")
def root():
    return {"message": "Automation OS"}
