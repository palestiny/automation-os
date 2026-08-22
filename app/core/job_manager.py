from uuid import uuid4
from datetime import datetime


class JobManager:

    def __init__(self):

        self.jobs = {}

    def create_job(self):

        job_id = str(uuid4())

        now = datetime.utcnow().isoformat()

        self.jobs[job_id] = {

            "id": job_id,

            "status": "pending",

            "progress": 0,

            "title": None,

            "message": "Waiting to start",

            "error": None,

            "created_at": now,

            "updated_at": now
        }

        return job_id

    def update_progress(
        self,
        job_id: str,
        progress: int,
        status: str | None = None,
        message: str | None = None
    ):

        if job_id not in self.jobs:
            return

        job = self.jobs[job_id]

        job["progress"] = progress

        if status:
            job["status"] = status

        if message:
            job["message"] = message

        job["updated_at"] = datetime.utcnow().isoformat()

    def set_title(
        self,
        job_id: str,
        title: str
    ):

        if job_id not in self.jobs:
            return

        self.jobs[job_id]["title"] = title

    def set_error(
        self,
        job_id: str,
        error: str
    ):

        if job_id not in self.jobs:
            return

        job = self.jobs[job_id]

        job["status"] = "failed"

        job["error"] = error

        job["updated_at"] = datetime.utcnow().isoformat()

    def complete(
        self,
        job_id: str,
        message: str = "Completed successfully"
    ):

        if job_id not in self.jobs:
            return

        job = self.jobs[job_id]

        job["progress"] = 100

        job["status"] = "completed"

        job["message"] = message

        job["updated_at"] = datetime.utcnow().isoformat()

    def get_job(self, job_id: str):

        return self.jobs.get(job_id)